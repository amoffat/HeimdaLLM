from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects("postgres")
def test_type_cast(dialect: str, Bifrost: Type[Bifrost]):
    """Prove prefix type casts are allowed"""
    # FIXME this doesn't do what is advertised
    raise NotImplementedError
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT
    movies.title,
    movies.release_date,
    movies.description
FROM
    movies
WHERE
    movies.search @@ websearch_to_tsquery('english', 'world war') AND
    movies.release_date >= DATE '1990-01-01' AND
    movies.release_date < DATE '2000-01-01' AND
    movies.budget IS NOT NULL AND
    movies.revenue IS NOT NULL AND
    movies.budget >= 1000
"""
    bifrost.traverse(query)
