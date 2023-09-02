from weakref import proxy

from lark import Tree, Visitor


class ParentSetter(Visitor):
    """
    Sets the `parent` attribute on all child nodes of a tree. This is useful for
    detecting if we're in a subquery or not.
    """

    def __default__(self, tree: Tree):
        for subtree in tree.children:
            if isinstance(subtree, Tree):
                assert not hasattr(subtree.meta, "parent")
                subtree.meta.parent = proxy(tree)  # type: ignore
