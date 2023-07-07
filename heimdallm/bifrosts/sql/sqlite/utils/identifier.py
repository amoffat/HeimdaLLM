from typing import cast

from lark import Token, Tree

from ... import exc
from ..presets import reserved_keywords


def get_identifier(node, throw_exc=True) -> str:
    """takes some node from the tree, either a token or a subtree, and finds
    the identifier it contains. this is used for the rule that matches an
    identifier or a quoted identifier, because, in that case, an identifier will
    be a token, and a quoted identifier will be a subtree containing an
    identifier token.

    also we check to make sure that the identifier is not a reserved keyword, as
    a convenience. we could do it a separate step, but it's easier to do it
    here."""

    def match_ident(v):
        return isinstance(v, Token) and v.type == "IDENTIFIER"

    quoted = False
    ident = next(node.scan_values(match_ident)).value
    quoted = bool(list(node.find_data("quoted_identifier")))
    if throw_exc and not quoted and ident.lower() in reserved_keywords:
        raise exc.ReservedKeyword(keyword=ident)
    return ident


def is_count_function(node: Tree | Token) -> bool:
    """
    A helper for determining if a node is a *safe* aggregate function. We allow safe
    aggregate functions in the SELECT clause, because they don't reveal extra
    information.
    """
    if isinstance(node, Tree):
        if node.data == "aliased_column":
            node = node.children[0]

    if isinstance(node, Tree) and node.data == "function":
        fn_name = cast(Token, node.children[0].children[0]).value.lower()
        if fn_name == "count":
            return True
    return False
