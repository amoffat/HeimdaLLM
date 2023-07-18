from lark import Tree


def get_ancestor(node: Tree, ancestor_name: str) -> Tree | None:
    while node.parent:
        if node.parent.data == ancestor_name:
            return node.parent
        node = node.parent
    return None


def in_subquery(node: Tree) -> bool:
    return get_ancestor(node, "subquery") is not None
