from typing import Any, cast

from lark import Token, Tree


def get_ancestor(node: Tree, ancestor_name: str) -> Tree | None:
    while parent := cast(Any, node.meta).parent:
        if parent.data == ancestor_name:
            return parent
        node = cast(Any, node.meta).parent
    return None


def in_subquery(node: Tree) -> bool:
    return get_ancestor(node, "subquery") is not None


def has_subquery(node: Tree | Token) -> bool:
    if isinstance(node, Token):
        return False

    try:
        next(node.find_data("full_query"))
    except StopIteration:
        return False
    else:
        return True
