from typing import cast

from lark import Discard, Token
from lark import Transformer as _Transformer
from lark import Tree

from . import exc
from .common import FqColumn
from .utils.identifier import get_identifier, is_count_function
from .validator import ConstraintValidator
from .visitors.aliases import AliasCollector


def _build_limit_tree(limit, offset=None):
    children = [
        Token("LIMIT", "LIMIT"),
        Tree(
            "limit",
            [Token("NUMBER", limit)],
        ),
    ]
    if offset:
        children.extend(
            [
                Token("OFFSET", "OFFSET"),
                Tree(
                    "offset",
                    [Token("NUMBER", offset)],
                ),
            ]
        )
    return Tree("limit_clause", children)


def add_limit(limit_placeholder, max_limit: int):
    """ensures that a limit exists on the limit placeholder, and that it is not
    greater than the max limit"""

    # existing limit? test and maybe replace it
    if limit_placeholder.children:
        current_limit = int(
            cast(Token, next(limit_placeholder.find_data("limit")).children[0]).value
        )

        try:
            offset_node = next(limit_placeholder.find_data("offset"))
        except StopIteration:
            current_offset = 0
        else:
            current_offset = int(cast(Token, offset_node.children[0]).value)

        if current_limit > max_limit:
            limit_tree = _build_limit_tree(max_limit, current_offset)
            limit_placeholder.children[0] = limit_tree

    # adding a limit? just append it
    else:
        limit_tree = _build_limit_tree(max_limit)
        limit_placeholder.children.append(limit_tree)


def qualify_column(fq_column: FqColumn) -> Tree:
    """Replaces an alias node with a fully qualified column node."""
    tree = Tree(
        "fq_column",
        [
            Tree(
                Token("RULE", "table_name"),
                [
                    Tree(
                        Token("RULE", "unquoted_identifier"),
                        [Token("IDENTIFIER", fq_column.table)],
                    )
                ],
            ),
            Tree(
                Token("RULE", "column_name"),
                [
                    Tree(
                        Token("RULE", "unquoted_identifier"),
                        [Token("IDENTIFIER", fq_column.column)],
                    )
                ],
            ),
        ],
    )
    return tree


class ReconstructTransformer(_Transformer):
    """makes some alterations to a query if it does not meet some basic validation
    constraints, but could with those alterations. currently, these are just the
    following:

        - adding or lowering a limit on the number of rows
        - removing illegal selected columns
    """

    def __init__(self, validator: ConstraintValidator, reserved_keywords: set[str]):
        self._validator = validator
        self._collector = AliasCollector(reserved_keywords=reserved_keywords)
        self._last_discarded_column: FqColumn | None = None
        self._reserved_keywords = reserved_keywords
        super().__init__()

    def transform(self, tree):
        self._collector.visit(tree)
        return super().transform(tree)

    def select_statement(self, children):
        """checks if a limit needs to be added or adjusted"""
        max_limit = self._validator.max_limit()

        if max_limit is not None:
            for child in children:
                if not isinstance(child, Tree):
                    continue

                if child.data == "limit_placeholder":
                    add_limit(child, max_limit)
                    break

        return Tree("select_statement", children)

    def selected_columns(self, children):
        # if there's no children, it means we discarded every column selected, meaning
        # that they were all illegal columns. since we can't proceed without a column,
        # go ahead and raise an exception about illegal column.
        if not children:
            raise exc.IllegalSelectedColumn(column=self._last_discarded_column.name)
        return Tree("selected_columns", children)

    def column_alias(self, children: list[Tree | Token]):
        alias_name = get_identifier(children[0], self._reserved_keywords)

        # if we can't find the actual table where this column alias comes from, assume
        # the selected table.
        fq_columns = self._collector._aliased_columns[alias_name]

        # None means the alias is not based on any column (it's an expression of some
        # kind), so we leave this node alone
        if fq_columns is None:
            tree = Tree("column_alias", children)

        # if we haven't found any columns associated with this alias, it means that the
        # query is implicitly using the selected table, so we can fully qualify it based
        # on that information.
        elif len(fq_columns) == 0:
            tree = qualify_column(
                FqColumn(
                    table=cast(str, self._collector._selected_table),
                    column=alias_name,
                )
            )

        # if there's only one fq column associated with this alias, then we know it's
        # not a composite alias, so we can fully qualify it.
        elif len(fq_columns) == 1:
            tree = qualify_column(next(iter(fq_columns)))

        # if it's a composite alias, we can't fully qualify it, so we leave it alone.
        elif len(fq_columns) > 1:
            tree = Tree("column_alias", children)

        else:
            assert False, "Unreachable"

        return tree

    def selected_column(self, children: list[Tree | Token]):
        """ensures that every selected column is allowed"""
        selected = children[0]
        if is_count_function(selected):
            pass

        elif isinstance(selected, Tree):
            for fq_column_node in selected.find_data("fq_column"):
                table_node, column_node = fq_column_node.children

                maybe_table_alias = get_identifier(table_node, self._reserved_keywords)
                column_name = get_identifier(column_node, self._reserved_keywords)

                table_name = self._collector._aliased_tables.get(
                    maybe_table_alias, maybe_table_alias
                )
                column = FqColumn(table=table_name, column=column_name)
                if not self._validator.select_column_allowed(column):
                    self._last_discarded_column = column
                    return Discard

        return Tree("selected_column", children)


def postproc(items):
    """helps format our reconstructed query so it's not all on one line"""
    for item in items:
        if isinstance(item, Token):
            if item.type in {
                "FROM",
                "GROUP_BY",
                "HAVING",
                "INNER_JOIN",
                "LIMIT",
                "OFFSET",
                "ORDER_BY",
                "WHERE",
                "WHERE_TYPE",
            }:
                yield "\n"
            else:
                pass

        yield item

        if isinstance(item, Token):
            if item.type in {}:
                yield " "
