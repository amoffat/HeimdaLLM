from collections import defaultdict as dd
from typing import Any, cast
from uuid import UUID

from lark import Tree, Visitor

from ..common import FqColumn
from ..exc import AliasConflict
from ..utils.identifier import get_identifier, is_count_function, is_subquery


class _QueryAliases:
    """These are aliases for tables and columns contained in a query. Each top-level
    query may have several QueryAlias objects, if the query contains subqueries, because
    each subquery has its own set of aliases which must be kept distinct from the
    top-level aliases.

    Essentially, this represents the "scope" of all the aliases that can be seen by the
    current query.
    """

    def __init__(self: "_QueryAliases"):
        # aliased table names from the FROM clause, as well as JOIN clauses.
        # they map from the alias name to a set of table names. It's a set because an
        # alias may be mapped to multiple different tables, and we want to detect this
        # so that we can raise an exception.
        #
        # also, in addition to the keys being aliases, the keys may be authoritative
        # table names themselves.
        self.tables: dict[str, set[str]] = dd(set)
        # aliased column names from the SELECT clause. they map from the alias name to
        # the a collection of fully qualified column names. the reason why it's a
        # collection is because a single alias can be a composite alias consisting of
        # multiple columns, for example, ``(a + b) as c``.
        #
        # a None value means that the alias cannot have any associated columns, which
        # can happen for aliases based on an expression, and not columns.
        #
        # each FqColumn in the set may contain aliases themselves, which is why we need
        # to resolve them in the .resolve() method.
        self.columns: dict[str, set[FqColumn] | None] = dd(set)
        # these represent subqueries that are aliased in the FROM and JOIN clauses. the
        # key is the alias for the subquery, and the value is the uuid associated with
        # the subquery node.
        self.subqueries: dict[str, UUID] = {}
        # this is used to help resolve unqualified column names to their fully qualified
        # name, if possible.
        self.selected_table: str | None = None


class AliasCollector(Visitor):
    """Collects all of our table and column aliases, which can then be mapped back to
    the authoritative names. We have to do this pass first, before any other passes,
    because the tree may not evaluate in the order that would allow us to resolve
    aliases."""

    def __init__(self, reserved_keywords: set[str]):
        self._query_aliases: dict[UUID, _QueryAliases] = {}
        self._reserved_keywords = reserved_keywords
        self._table_aliases: dict[str, str] = {}

    def visit(self, tree: Tree) -> Tree:
        new_tree = super().visit(tree)
        self._resolve_aliases()
        return new_tree

    def _resolve_aliases(self):
        """Processes all aggregated aliases, and resolves them to their authoritative
        names."""

        table_aliases = {}
        self._table_aliases = table_aliases

        # first collect all of the table aliases that we know of. we'll also test that
        # there exist only one authoritative table name associated with each alias.
        for qa in self._query_aliases.values():
            for alias, auth_tables in qa.tables.items():
                if len(auth_tables) > 1:
                    raise AliasConflict(alias)
                table_aliases[alias] = next(iter(auth_tables))

        # look at the aliases for derived queries (aliased subqueries) and ensure that
        # they don't conflict with any other aliases. we don't actually do anything with
        # the derived query aliases, because they don't resolve to anything that isn't
        # covered by other validations. for example, if `t1` aliases to a subquery,
        # that subquery is already checked for selectable tables and columns
        for qa in self._query_aliases.values():
            for alias in qa.subqueries.keys():
                if alias in table_aliases:
                    raise AliasConflict(alias)

        # now that we've collected all of the aliases, we can resolve fully-qualfiied
        # column names that may have an alias for their table component.
        for qa in self._query_aliases.values():
            for fq_columns in qa.columns.values():
                if fq_columns:
                    for fq_column in fq_columns:
                        if fq_column.table in table_aliases:
                            fq_column.table = table_aliases[fq_column.table]

        # TODO resolve qa.selected_table
        pass

    def resolve_table(self, table: str) -> str:
        """For a table name, resolve it to its authoritative name."""
        return self._table_aliases.get(table, table)

    def alias_scope(self, node: Tree) -> _QueryAliases:
        """Finds the wrapping query for a given node, and returns the aliases for it.
        This is the scope of aliases that are available to the current node."""
        p = cast(Any, node.meta).parent
        while p is not None:
            if p.data == "full_query":
                aliases = self._query_aliases.setdefault(p.meta.id, _QueryAliases())
                return aliases

            p = p.meta.parent
        raise RuntimeError("could not find wrapping query for node")

    def selected_table(self, node: Tree):
        """Called for tables targeted in the FROM clause of a SELECT statement."""
        aliases = self.alias_scope(node)
        table_type_node = node.children[0]

        # if we're selecting from a normal table, then use its name
        if table_type_node.data == "table_name":
            table_name = get_identifier(node, self._reserved_keywords)
            aliases.selected_table = table_name
            aliases.tables[table_name].add(table_name)

        # it's a derived table, aka an aliased subquery
        elif table_type_node.data == "derived_table":
            subquery, _as, alias_node = table_type_node.children
            alias_name = get_identifier(alias_node, self._reserved_keywords)
            aliases.selected_table = alias_name
            sq_node = subquery.children[0]
            aliases.subqueries[alias_name] = cast(Any, sq_node.meta).id

        elif table_type_node.data == "aliased_table":
            table_node, _as, alias_node = table_type_node.children
            table_name = get_identifier(table_node, self._reserved_keywords)
            alias = get_identifier(alias_node, self._reserved_keywords)
            aliases.tables[alias].add(table_name)

    joined_table = selected_table

    def full_query(self, node: Tree):
        self._query_aliases.setdefault(cast(Any, node.meta).id, _QueryAliases())

    def aliased_column(self, node: Tree):
        """Columns are aliased in the column list of a SELECT statement. we assume
        that all aliased columns are fully qualified by table name. note, however, that
        the table name may be an alias itself."""
        aliases = self.alias_scope(node)
        value_node, _as, alias_node = node.children
        alias_name = get_identifier(alias_node, self._reserved_keywords)

        # if it's a count function, we don't care what it's composed of, because it
        # doesn't reveal any information about the underlying data. so we don't use it
        # for resolving aliases
        if is_count_function(value_node):
            aliases.columns[alias_name] = None
            return

        # if it's a subquery, we'll need to dig into the subquery later to figure out
        # exactly what the alias name refers to. for now, just store a reference to the
        # subquery and move on.
        if is_subquery(value_node):
            aliases.subqueries[alias_name] = cast(Any, value_node.meta).id
            return

        # there may be multiple columns referenced in this alias column, for
        # example if we're running a function on multiple columns and aliasing
        # the result. so we need to look at each fq_column individually
        inserted_fq_alias = False
        for fq_column_node in value_node.find_data("fq_column"):
            table_node, column_node = fq_column_node.children
            table_name = get_identifier(table_node, self._reserved_keywords)
            column_name = get_identifier(column_node, self._reserved_keywords)

            # do we already have a table alias for this column? use that instead for
            # the table name
            composite_columns = cast(set[FqColumn], aliases.columns[alias_name])
            composite_columns.add(FqColumn(table=table_name, column=column_name))
            inserted_fq_alias = True

        # if we didn't insert an alias at this point, it means it's an expression that
        # is being an aliased. something like ``1 + 1 as name``. so we set it to None so
        # that we don't try to autofix it later to be a fully qualified column.
        if not inserted_fq_alias:
            aliases.columns[alias_name] = None
