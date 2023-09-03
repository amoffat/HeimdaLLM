from uuid import uuid4

from lark import Tree, Visitor


class IdSetter(Visitor):
    """
    Sets the `id` attribute on all child nodes of a tree. This is useful operations that
    require us to store tree nodes in a mapping, keyed by id.
    """

    def __default__(self, tree: Tree):
        if not hasattr(tree.meta, "id"):
            tree.meta.id = uuid4()  # type: ignore
