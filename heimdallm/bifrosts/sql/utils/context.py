from typing import Any, cast

from lark import Tree


def get_ancestor(node: Tree, ancestor_name: str) -> Tree | None:
    while parent := cast(Any, node.meta).parent:
        if parent.data == ancestor_name:
            return parent
        node = cast(Any, node.meta).parent
    return None


def in_subquery(node: Tree) -> bool:
    return get_ancestor(node, "subquery") is not None
