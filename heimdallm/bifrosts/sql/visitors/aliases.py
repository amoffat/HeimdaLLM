from collections import defaultdict as dd
from typing import cast

from lark import Tree, Visitor

from ..common import FqColumn
from ..utils.identifier import get_identifier, is_count_function


class AliasCollector(Visitor):
    """collects all of our table and column aliases and maps them back to the
    authoritative name. we have to do this pass first, before any other passes,
    because the tree may not evaluate in the order that would allow us to
    resolve aliases."""

    def __init__(self, reserved_keywords: set[str]):
        # aliased table names from the FROM clause, as well as JOIN clauses.
        # they map from the alias name to the table name.
        self._aliased_tables: dict[str, str] = {}
        # aliased column names from the SELECT clause. they map from the alias name to
        # the a collection of fully qualified column names. the reason why it's a
        # collection is because a single alias can be a composite alias consisting of
        # multiple columns, for example, ``(a + b) as c``.
        #
        # a None value means that the alias cannot have any associated columns, which
        # can happen for aliases based on an expression, and not columns.
        self._aliased_columns: dict[str, set[FqColumn] | None] = dd(set)
        self._reserved_keywords = reserved_keywords
        self._selected_table: str | None = None

    def _resolve_table(self, table):
        return self._aliased_tables.get(table, table)

    def selected_table(self, node: Tree):
        self._selected_table = get_identifier(node, self._reserved_keywords)

    # tables are aliased in the FROM clause of a SELECT statement, or when a
    # table is JOINed. it's here that we know the authoritative table name and
    # its alias, which may be used in other parts of the query
    def aliased_table(self, node: Tree):
        table_node, _as, alias_node = node.children
        table_name = get_identifier(table_node, self._reserved_keywords)
        alias = get_identifier(alias_node, self._reserved_keywords)
        self._aliased_tables[alias] = table_name

        # inefficient, but backfill the correct table alias for any columns. we must do
        # some form of this because we may have recorded a column alias, e.g. ``r.amt as
        # amt``, before knowing the table alias, e.g. ``rental as r``. so for each
        # aliased table that we resolve, we need to make sure the column aliases reflect
        # that table alias correctly. this could be more efficient.
        for fq_columns in self._aliased_columns.values():
            if fq_columns:
                for fq_column in fq_columns:
                    if fq_column.table == alias:
                        fq_column.table = table_name

    # columns are aliased in the column list of a SELECT statement. we assume
    # that all aliased columns are fully qualified by table name. note, however,
    # that the table name may be an alias itself.
    def aliased_column(self, node: Tree):
        value_node, _as, alias_node = node.children
        alias_name = get_identifier(alias_node, self._reserved_keywords)

        # if it's a count function, we don't care what it's composed of, because it
        # doesn't reveal any information about the underlying data. so we don't use it
        # for resolving aliases
        if is_count_function(value_node):
            self._aliased_columns[alias_name] = None
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
            table_name = self._resolve_table(table_name)
            composite_columns = cast(set[FqColumn], self._aliased_columns[alias_name])
            composite_columns.add(FqColumn(table=table_name, column=column_name))
            inserted_fq_alias = True

        # if we didn't insert an alias at this point, it means it's an expression that
        # is being an aliased. something like ``1 + 1 as name``. so we set it to None so
        # that we don't try to autofix it later to be a fully qualified column.
        if not inserted_fq_alias:
            self._aliased_columns[alias_name] = None
