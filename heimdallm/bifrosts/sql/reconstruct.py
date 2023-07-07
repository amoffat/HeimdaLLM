from typing import cast

from lark import Discard, Token
from lark import Transformer as _Transformer
from lark import Tree

from . import exc
from .sqlite.utils.identifier import get_identifier, is_count_function
from .sqlite.utils.visitors import AliasCollector
from .utils import FqColumn
from .validator import ConstraintValidator


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


class ReconstructTransformer(_Transformer):
    """makes some alterations to a query if it does not meet some basic validation
    constraints, but could with those alterations. currently, these are just the
    following:

        - adding or lowering a limit on the number of rows
        - removing illegal selected columns
    """

    def __init__(self, validator: ConstraintValidator):
        self._validator = validator
        self._collector = AliasCollector()
        self._last_discarded_column = None
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

    def selected_column(self, children):
        """ensures that every selected column is allowed"""
        selected = children[0]
        if is_count_function(selected):
            pass

        elif isinstance(selected, Tree):
            for fq_column_node in selected.find_data("fq_column"):
                table_node, column_node = fq_column_node.children

                maybe_table_alias = get_identifier(table_node)
                column_name = get_identifier(column_node)

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
