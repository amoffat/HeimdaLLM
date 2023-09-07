from collections import defaultdict as dd
from typing import Any, MutableMapping, Optional, cast
from uuid import UUID

from lark import Token, Tree, Visitor

from heimdallm.bifrosts.sql.utils.context import has_subquery, in_subquery

from .. import exc
from ..common import FqColumn, JoinCondition, RequiredConstraint
from ..utils.identifier import get_identifier, is_count_function
from .aliases import AliasCollector


class Facets:
    """this simple class is used to collect all of the facets of a query, so
    that we can easily validate them with a constraint validator"""

    def __init__(self) -> None:
        # tables that were joined but do not reference the table in the join
        # condition. if this list has values, validation fails.
        self.bad_joins: list[str] = []
        # the table selected in the FROM clause. this will always be set after a
        # successful parse
        self.selected_table: Optional[str] = None
        # the tables joined to the query, this could include the table selected
        # in the FROM clause, if there are JOINs in the query
        self.joined_tables: MutableMapping[str, set[JoinCondition]] = dd(set)
        # the columns selected in the query
        self.selected_columns: set[FqColumn] = set()
        # the columns used in the WHERE, JOIN, HAVING, and ORDER BY clauses
        self.condition_columns: set[FqColumn] = set()
        # the required conditions in the WHERE and JOIN clauses, used to
        # constrain the query so that it is safe
        self.required_constraints: set[RequiredConstraint] = set()
        # all of the functions used in the query
        self.functions: set[str] = set()
        # the row limit of the query and all subqueries
        self.limits: dict[UUID, int | None] = {}


class FacetCollector(Visitor):
    """collects all of the facets of the query that we care about. this will
    feed directly into the constraint validator"""

    def __init__(
        self,
        facets: Facets,
        collector: AliasCollector,
        reserved_keywords: set[str],
    ):
        self._collector = collector
        self._facets = facets
        self._reserved_keywords = reserved_keywords

    def _resolve_column(self, node: Tree) -> set[FqColumn] | None:
        if node.data == "column_alias":
            maybe_alias = get_identifier(node, self._reserved_keywords)
            aliases = self._collector.alias_scope(node)
            return aliases.columns[maybe_alias]

        # should never happen
        raise RuntimeError(f"unknown column reference type: {type(node)}")

    def _resolve_table(self, table_ref: Tree | Token) -> str | None:
        if isinstance(table_ref, Tree):
            # it's clearly an aliased table, so we know the table name from this node
            if table_ref.data == "aliased_table":
                table_name = get_identifier(table_ref, self._reserved_keywords)
                return table_name

            # it's a table name, but it may be an alias, so we need to do a lookup
            elif table_ref.data == "table_name":
                maybe_alias = get_identifier(table_ref, self._reserved_keywords)
                table = self._collector.resolve_table(maybe_alias)
                return table

        elif isinstance(table_ref, Token):
            return table_ref.value

        # should never happen
        raise RuntimeError(f"unknown table reference type: {type(table_ref)}")

    def join(self, node: Tree):
        if join_type_nodes := list(node.find_data("illegal_join")):
            join_type = cast(Token, join_type_nodes[0].children[0]).type
            raise exc.IllegalJoinType(join_type=join_type)

        joined_table = node.children[1].children[0]
        joined_table_name = self._resolve_table(joined_table)

        if joined_table_name is None:
            raise exc.UnsupportedQuery(msg="JOIN on derived table")

        # if a required_comparison node exists, it means it is actually required
        # (enforced by the grammar, see grammar comments). a required comparison has
        # a placeholder for the RHS
        for required_comparison in node.find_data("required_comparison"):
            self._add_required_comparison(required_comparison)

        for condition in node.find_data("connecting_join_condition"):
            # from_table may be an alias, but from_column will always be authoritative.
            # the LHS of the join condition is always a fully-qualified column
            from_fq_column_node = condition.children[0]
            from_table_node, from_column_node = from_fq_column_node.children
            from_column = get_identifier(from_column_node, self._reserved_keywords)
            from_table = self._resolve_table(from_table_node)
            if from_table is None:
                raise exc.UnsupportedQuery(msg="JOIN condition on derived table")

            # conditions in a join are compared against are allowed conditions, so
            # record the LHS
            self._collect_condition_column(from_fq_column_node)

            # to_table may be an alias, but to_column will always be authoritative.
            # the RHS of the join condition can be a `value` rule.
            to_fq_column_node = condition.children[2]

            # token? it's probably a string or number, keep going
            if isinstance(to_fq_column_node, Token):
                continue
            # not a fq column? it's probably a function or something nested, keep going.
            elif (
                isinstance(to_fq_column_node, Tree)
                and to_fq_column_node.data != "fq_column"
            ):
                continue

            to_table, to_column_node = to_fq_column_node.children
            to_column = get_identifier(to_column_node, self._reserved_keywords)

            to_table = self._resolve_table(to_table)
            if to_table is None:
                raise exc.UnsupportedQuery(msg="JOIN condition on derived table")

            # the joined table must be one of the parts of the join condition
            if joined_table_name != from_table and joined_table_name != to_table:
                self._facets.bad_joins.append(joined_table_name)
                continue

            # conditions in a join are compared against are allowed conditions, so
            # record the RHS
            self._collect_condition_column(to_fq_column_node)

            # our join represents two sides, the from table and the to table.
            # we'll record both in our joined_tables set.
            join_spec = JoinCondition(
                f"{from_table}.{from_column}",
                f"{to_table}.{to_column}",
            )
            self._facets.joined_tables[from_table].add(join_spec)
            self._facets.joined_tables[to_table].add(join_spec)

    def selected_table(self, node: Tree):
        table_node = list(node.find_data("table_name"))[0]
        table_name = get_identifier(table_node, self._reserved_keywords)
        self._facets.selected_table = table_name

    def selected_column(self, node: Tree):
        child = node.children[0]

        if isinstance(child, Token) and child.type == "COUNT_STAR":
            return

        elif isinstance(child, Token) and child.type == "ALL_COLUMNS":
            raise exc.IllegalSelectedColumn(column="*")

        # if we're aliasing COUNT(*), it's safe to ignore, since it doesn't
        # reveal any of the underlying values
        elif is_count_function(child):
            return

        elif isinstance(child, Tree):
            # if it's an aliased column, we need to ensure that the thing being aliased
            # isn't a non-fully-qualified column. we do that by looking for
            # `generic_alias`
            if child.data == "aliased_column":
                alias_child = child.children[0]
                # if we're aliasing COUNT(*), it's safe to ignore, since it doesn't
                # reveal any of the underlying values
                if isinstance(alias_child, Token) and alias_child.type == "COUNT_STAR":
                    return

                if list(alias_child.find_data("generic_alias")):
                    alias = get_identifier(alias_child, self._reserved_keywords)
                    raise exc.UnqualifiedColumn(column=alias)

            # if the column looks like a column alias (meaning a non-fully-qualified
            # column), then that's an error, because we only work with fully-qualified
            # columns
            elif child.data == "generic_alias":
                alias = get_identifier(child, self._reserved_keywords)
                raise exc.UnqualifiedColumn(column=alias)

            # if we're not an aliased column, but we contain a column alias somewhere,
            # that's an error, because we only work with fully-qualified columns
            elif column_alias := list(child.find_data("generic_alias")):
                alias = get_identifier(column_alias[0], self._reserved_keywords)
                raise exc.UnqualifiedColumn(column=alias)

            # if we've made it this far, we're sure we're dealing with a fully-qualified
            # column, or a non-column based expression
            if has_subquery(child):
                return

            try:
                table_node = next(child.find_data("table_name"))
            # it's some non-column expression, which we don't care about
            except StopIteration:
                pass
            # there's a fully qualified column there, so we'll record it
            else:
                table_name = self._resolve_table(table_node)

                # a none indicates that the table points to a derived table. we don't
                # count that as a selected column, because we do separate validation on
                # derived tables.
                if table_name is None:
                    return

                # column_name will always be authoritative, even if it is aliased in
                # this node
                column_name = get_identifier(
                    list(child.find_data("column_name"))[0],
                    self._reserved_keywords,
                )
                self._facets.selected_columns.add(
                    FqColumn(
                        table=table_name,
                        column=column_name,
                    )
                )

    def _add_required_comparison(self, node: Tree):
        """takes a node representing a required comparison and adds it to the
        facets"""

        # if we're in a subquery, don't count it as a required comparison, because a
        # required comparison must exist in the outermost query
        if in_subquery(node):
            return

        # handle both a forwards (column = :placeholder) and backwards (:placeholder =
        # column)
        if list(node.find_data("lhs_req_comparison")):
            maybe_fq_column_node, placeholder = node.children[0].children
        else:
            placeholder, maybe_fq_column_node = node.children[0].children

        placeholder_name = cast(Token, placeholder.children[0]).value

        if maybe_fq_column_node.data == "column_alias":
            maybe_fq_columns = self._resolve_column(maybe_fq_column_node)

            # none means the alias is based on an expression, so we don't need to add it
            # to the required constraints because it's not a column
            if maybe_fq_columns is None:
                return

            # multiple columns means the alias is based on a composite expression, so we
            # cannot determine which column to add to the required constraints, so we
            # add none of them
            elif len(maybe_fq_columns) > 1:
                return

            # no columns means the alias was never resolved. i don't think we should
            # ever end up down this path
            elif len(maybe_fq_columns) == 0:
                assert False, "Unreachable"

            # otherwise we have one column backing the alias, so we add it to the
            # required constraints that were found.
            elif len(maybe_fq_columns) == 1:
                fq_column = next(iter(maybe_fq_columns))
                self._facets.required_constraints.add(
                    RequiredConstraint(
                        column=fq_column.name,
                        placeholder=placeholder_name,
                    )
                )

        elif maybe_fq_column_node.data == "fq_column":
            fq_column_node = maybe_fq_column_node
            table_node, column_node = fq_column_node.children

            table_name = self._resolve_table(table_node)
            column_name = get_identifier(column_node, self._reserved_keywords)

            self._facets.required_constraints.add(
                RequiredConstraint(
                    column=f"{table_name}.{column_name}",
                    placeholder=placeholder_name,
                )
            )
        else:
            raise RuntimeError(
                f"Unknown required column type {type(maybe_fq_column_node)}"
            )

    def where_clause(self, where_node: Tree):
        """here we'll do a breadth-first search on the where clause, going level
        by level. if any level contains an "OR", that means the entire level is
        tainted and can't be used for a required constraint, because the
        required constraint may be optional.

        if a level is tainted, then all of its children (WHERE subclauses) are
        tainted as well, so we will not process them.

        the end result is that we only collect a required comparison node IFF it
        is not joined by an OR anywhere in the WHERE clause, either at its
        level, or at any level above it. only then can we know that the
        comparison is actually constraining to the query"""
        conditions = where_node.children[1]
        stack: list[Tree] = [conditions]

        while stack:
            conditions = stack.pop()

            level_stack: list[Tree] = []
            for child in conditions.children:
                if isinstance(child, Token):
                    # is the level tainted? if so, clear the stack and exit the loop
                    if child.type == "WHERE_TYPE" and child.value.lower() == "or":
                        level_stack = []
                        break
                elif isinstance(child, Tree):
                    level_stack.append(child)

            for child in reversed(level_stack):
                stack.append(child)
                if child.data == "required_comparison":
                    self._add_required_comparison(child)

    def _collect_condition_column(self, node: Tree):
        """here we'll parse out the columns that are referenced anywhere in the
        WHERE, regardless of the depth of the expression. we care if a column is being
        referenced at all, even optionally, because that will be checked against the
        allowlist"""
        for fq_column_node in node.find_data("fq_column"):
            table_node, column_node = fq_column_node.children
            table_name = self._resolve_table(table_node)
            if table_name is None:
                raise exc.UnsupportedQuery(msg="WHERE condition on derived table")

            column_name = get_identifier(column_node, self._reserved_keywords)
            self._facets.condition_columns.add(
                FqColumn(
                    table=table_name,
                    column=column_name,
                )
            )

        for column_alias_node in node.find_data("column_alias"):
            maybe_fq_columns = self._resolve_column(column_alias_node)

            # a None means this is a non-column expression alias. this is valid as it
            # is, so we don't raise, and we don't track it as a condition column.
            if maybe_fq_columns is None:
                pass
            # we have a single underlying column, or multiple composite columns. add all
            # of them to our condition columns.
            elif len(maybe_fq_columns) > 0:
                self._facets.condition_columns.update(maybe_fq_columns)
            # we have no columns that resolve the alias. this is an error.
            else:
                column_name = get_identifier(column_alias_node, self._reserved_keywords)
                raise exc.UnqualifiedColumn(column=column_name)

    where_condition = _collect_condition_column
    having_condition = _collect_condition_column
    order_column = _collect_condition_column

    def limit_placeholder(self, node: Tree):
        if limit_nodes := list(node.find_data("limit")):
            limit_node = limit_nodes[0]
            limit = int(cast(Token, limit_node.children[0]).value)
        else:
            limit = None
        self._facets.limits[cast(Any, node.meta).id] = limit

    def function(self, node: Tree):
        self._facets.functions.add(cast(Token, node.children[0]).value.lower())
