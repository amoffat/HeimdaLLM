from lark import Transformer

from .. import exc
from ..utils.identifier import get_identifier


class AmbiguityResolver(Transformer):
    """this transformer's purpose is to resolve ambiguities in the parse tree
    that can only be resolved through some extra knowledge that would be
    difficult to embed in the grammar itself.
    """

    def __init__(self, query: str, reserved_keywords: set[str]):
        self.reserved_keywords = reserved_keywords
        self.query = query
        super().__init__()

    def test_alias(self, i, tree, trees) -> bool:
        """
        This resolves ambiguities in the parse tree related to aliases. For
        example, the following query is ambiguous:

            select t1.secret from t1 left join t2 on t1.jid = t2.jid

        Is "left" an alias for "t1", or is it part of the "left join"? It's
        ambiguous. We know it's not ambiguous because "left" is a keyword, but
        the parser can't know this. This class resolves those ambiguities by
        looking at all possible ambiguous parse trees in the ambiguity, and
        selecting only the one that does not have an alias conflict with a
        reserved keyword.
        """
        for alias_node in tree.find_data("generic_alias"):
            try:
                get_identifier(alias_node, self.reserved_keywords)
            except exc.ReservedKeyword:
                return False
        return True

    def test_req_comparisons(self, i, tree, trees) -> bool:
        """in a where_condition rule, the children can include
        `relational_comparison` and `parameterized_comparison` rules, which are
        ambiguous, because parameterized comparisons are a subset of relational
        comparisons. we always prefer to interpret the ambiguity as a parameterized
        comparison though, because it is more strict, and it satisfies our
        parameterized comparison validator constraints"""
        if tree.data in ("where_condition", "join_condition"):
            return tree.children[0].data == "parameterized_comparison"
        return True

    def test_arith_expr(self, i, tree, trees) -> bool:
        """the arith_expr node is recursive, so it can be ambiguous. just choose the
        first parse of it, since this node doesn't really matter"""
        if tree.data == "arith_expr":
            return i == 0
        return True

    def _ambig(self, trees):
        def test_tree(i, tree):
            return (
                self.test_alias(i, tree, trees)
                and self.test_req_comparisons(i, tree, trees)
                and self.test_arith_expr(i, tree, trees)
            )

        pruned_trees = [tree for i, tree in enumerate(trees) if test_tree(i, tree)]

        if len(pruned_trees) == 0:
            raise exc.InvalidQuery(query=self.query)
        elif len(pruned_trees) == 1:
            return pruned_trees[0]
        else:
            raise exc.AmbiguousParse(trees=pruned_trees, query=self.query)
