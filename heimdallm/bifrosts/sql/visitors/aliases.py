from lark import Token, Tree, Visitor

from ..utils.identifier import get_identifier


class AliasCollector(Visitor):
    """collects all of our table and column aliases and maps them back to the
    authoritative name. we have to do this pass first, before any other passes,
    because the tree may not evaluate in the order that would allow us to
    resolve aliases."""

    def __init__(self, reserved_keywords: set[str]):
        # aliased table names from the FROM clause, as well as JOIN clauses.
        # they map from the alias name to the table name.
        self._aliased_tables: dict[str, str] = {}
        # aliased column names from the SELECT clause. they map from the alias
        # name to the (table, column) tuple
        self._aliased_columns: dict[str, tuple[str | None, str | None]] = {}
        self._reserved_keywords = reserved_keywords

    def _resolve_table(self, table):
        return self._aliased_tables.get(table, table)

    # tables are aliased in the FROM clause of a SELECT statement, or when a
    # table is JOINed. it's here that we know the authoritative table name and
    # its aliased, which may be used in other parts of the query
    def aliased_table(self, node: Tree):
        table_node, _as, alias_node = node.children
        table_name = get_identifier(table_node, self._reserved_keywords)
        alias = get_identifier(alias_node, self._reserved_keywords)
        self._aliased_tables[alias] = table_name

        # inefficient, but backfill the correct table alias for any columns
        for key, (tn, cn) in list(self._aliased_columns.items()):
            if tn == alias:
                self._aliased_columns[key] = (table_name, cn)

    # columns are aliased in the column list of a SELECT statement. we assume
    # that all aliased columns are fully qualified by table name. note, however,
    # that the table name may be an alias itself.
    def aliased_column(self, node: Tree):
        value_node, _as, alias_node = node.children
        alias_name = get_identifier(alias_node, self._reserved_keywords)

        if isinstance(value_node, Token):
            if value_node.type == "COUNT_STAR":
                self._aliased_columns[alias_name] = (None, None)
            return

        # there may be multiple columns referenced in this alias column, for
        # example if we're running a function on multiple columns and aliasing
        # the result. so we need to look at each fq_column individually
        for fq_column_node in value_node.find_data("fq_column"):
            table_node, column_node = fq_column_node.children
            table_name = get_identifier(table_node, self._reserved_keywords)
            column_name = get_identifier(column_node, self._reserved_keywords)

            # do we already have a table alias for this column? use that instead for
            # the table name
            table_name = self._resolve_table(table_name)
            self._aliased_columns[alias_name] = (table_name, column_name)
