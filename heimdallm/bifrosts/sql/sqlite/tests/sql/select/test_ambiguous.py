from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import PermissiveConstraints


def test_ambiguous_arith():
    """arith_expr is recursive, so the parser can interpret a long chain of arithmetic
    operations as a single expression, or different groups of sub expressions. our
    ambiguity resolver picks the longest expression"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT
    c.customer_id,
    (1 + 2 + 3 + 4 + 5) AS num
FROM
    customer as c
WHERE
    c.customer_id = :customer_id
    """

    bifrost.traverse(query)
