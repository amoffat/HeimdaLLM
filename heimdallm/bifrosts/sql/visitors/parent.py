from typing import Any, cast
from weakref import proxy

from lark import Tree, Visitor


class ParentSetter(Visitor):
    """
    Sets the `parent` attribute on all child nodes of a tree. This is useful for
    detecting if we're in a subquery or not.
    """

    def __default__(self, tree: Tree):
        # this will get the root node, which has no parent
        if not hasattr(tree.meta, "parent"):
            cast(Any, tree.meta).parent = None

        for subtree in tree.children:
            if isinstance(subtree, Tree):
                subtree.meta.parent = proxy(tree)  # type: ignore
