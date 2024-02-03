from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_ambiguous_arith(dialect: str, Bifrost: Type[Bifrost]):
    """arith_expr is recursive, so the parser can interpret a long chain of arithmetic
    operations as a single expression, or different groups of sub expressions. our
    ambiguity resolver picks the longest expression"""
    bifrost = Bifrost.validation_only(PermissiveConstraints())

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


@dialects()
def test_ambiguous_bool(dialect: str, Bifrost: Type[Bifrost]):
    """A regression test to ensure that boolean tokens do not trigger the ambiguity
    resolver"""
    bifrost = Bifrost.validation_only(PermissiveConstraints())

    query = """
SELECT
    col
FROM
     postings AS p
WHERE
     p.is_hired = true
     """
    bifrost.traverse(query)
