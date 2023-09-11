from typing import Generator, Iterable, cast

from lark import Discard, Token, Tree, v_args
from lark.visitors import Transformer as _Transformer

from heimdallm.bifrosts.sql.utils.context import has_subquery, in_subquery
from heimdallm.context import TraverseContext

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


@v_args(tree=True)
class ReconstructTransformer(_Transformer):
    """makes some alterations to a query if it does not meet some basic validation
    constraints, but could with those alterations. currently, these are just the
    following:

        - adding or lowering a limit on the number of rows
        - removing illegal selected columns
    """

    def __init__(
        self,
        *,
        validator: ConstraintValidator,
        reserved_keywords: set[str],
        ctx: TraverseContext
    ):
        self._validator = validator
        self._collector = AliasCollector(reserved_keywords=reserved_keywords, ctx=ctx)
        self._last_discarded_column: FqColumn | None = None
        self._reserved_keywords = reserved_keywords
        self._ctx = ctx
        super().__init__()

    def transform(self, tree):
        self._collector.visit(tree)
        return super().transform(tree)

    def _copy_tree(self, tree: Tree) -> Tree:
        return Tree(tree.data, tree.children, tree.meta)

    def select_statement(self, tree: Tree):
        """checks if a limit needs to be added or adjusted"""
        if not in_subquery(tree):
            max_limit = self._validator.max_limit()

            if max_limit is not None:
                for child in tree.children:
                    if not isinstance(child, Tree):
                        continue

                    if child.data == "limit_placeholder":
                        add_limit(child, max_limit)
                        break

        return self._copy_tree(tree)

    def selected_columns(self, tree: Tree):
        # if there's no children, it means we discarded every column selected, meaning
        # that they were all illegal columns. since we can't proceed without a column,
        # go ahead and raise an exception about illegal column.
        if not tree.children:
            raise exc.IllegalSelectedColumn(
                column=cast(FqColumn, self._last_discarded_column).name,
                ctx=self._ctx,
            )
        return self._copy_tree(tree)

    def column_alias(self, tree: Tree):
        """Called for columns in a condition. Despite the name, it may not be an actual
        alias, but rather a column name."""
        alias_name = get_identifier(
            self._ctx,
            tree.children[0],
            self._reserved_keywords,
        )

        # if we can't find the actual table where this column alias comes from, assume
        # the selected table.
        aliases = self._collector.alias_scope(tree)
        fq_columns = aliases.columns.get(alias_name, set())

        # None means the alias is not based on any column (it's an expression of some
        # kind), so we leave this node alone
        if fq_columns is None:
            tree = self._copy_tree(tree)

        # if we haven't found any columns associated with this alias, it means that the
        # query is implicitly using the selected table, so we can fully qualify it based
        # on that information.
        # FIXME, but what if there was a JOIN? TEST THIS
        elif len(fq_columns) == 0:
            if alias_name in self._collector.derived_table_aliases:
                tree = self._copy_tree(tree)

            else:
                old_meta = tree.meta
                tree = qualify_column(
                    FqColumn(
                        table=cast(str, aliases.selected_table),
                        column=alias_name,
                    )
                )
                tree._meta = old_meta

        # if there's only one fq column associated with this alias, then we know it's
        # not a composite alias, so we can fully qualify it.
        elif len(fq_columns) == 1:
            old_meta = tree.meta
            tree = qualify_column(next(iter(fq_columns)))
            tree._meta = old_meta

        # if it's a composite alias, we can't fully qualify it, so we leave it alone.
        elif len(fq_columns) > 1:
            tree = self._copy_tree(tree)

        else:
            assert False, "Unreachable"

        return tree

    def selected_column(self, tree: Tree):
        """Drops disallowed columns from the query, rather than have them fail at
        constraint validation."""
        selected = tree.children[0]
        if is_count_function(selected):
            pass

        # if the column we're selecting is a derived table, then it doesn't make sense
        # to drop it, because it can't fail ``select_column_allowed`` validation.
        elif has_subquery(selected):
            pass

        elif isinstance(selected, Tree):
            for fq_column_node in selected.find_data("fq_column"):
                table_node, column_node = fq_column_node.children

                maybe_table_alias = get_identifier(
                    self._ctx,
                    table_node,
                    self._reserved_keywords,
                )
                column_name = get_identifier(
                    self._ctx,
                    column_node,
                    self._reserved_keywords,
                )

                table_name = self._collector.resolve_table(maybe_table_alias)
                if table_name is not None:
                    column = FqColumn(table=table_name, column=column_name)

                    if not self._validator.select_column_allowed(column):
                        self._last_discarded_column = column
                        return Discard

        return self._copy_tree(tree)


PostProcToken = Token | str


def postproc(items: Iterable[PostProcToken]) -> Generator[PostProcToken, None, None]:
    for token in items:
        if token == "_WS":
            yield " "
            continue
        yield token
