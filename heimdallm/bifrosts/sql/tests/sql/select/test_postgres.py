from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects("postgres")
def test_type_cast(dialect: str, Bifrost: Type[Bifrost]):
    """Prove prefix type casts are allowed"""
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


@dialects("postgres")
def test_nonstandard_functions(dialect: str, Bifrost: Type[Bifrost]):
    """Prove non-standard functions (with non-tranditional function syntax) are
    allowed"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT
    movies.title,
    movies.release_date,
    SUBSTRING(movies.description FROM 1 FOR 200) AS short_description
FROM
    movies
WHERE
    movies.search @@ websearch_to_tsquery('english', 'world war')
    AND EXTRACT(YEAR from movies.release_date) BETWEEN 1990 AND 1999
    AND movies.budget IS NOT NULL
    AND movies.budget >= 1000;
"""
    bifrost.traverse(query)


@dialects("postgres")
def test_cte_select_from(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
WITH regional_sales AS (
    SELECT region, SUM(amount) AS total_sales
    FROM orders
    GROUP BY region
), top_regions AS (
    SELECT region
    FROM regional_sales
    WHERE total_sales > (SELECT SUM(total_sales)/10 FROM regional_sales)
)
SELECT region,
       product,
       SUM(quantity) AS product_units,
       SUM(amount) AS product_sales
FROM orders
WHERE region IN (SELECT region FROM top_regions)
GROUP BY region, product;
"""
    bifrost.traverse(query)


@dialects("postgres")
def test_cte_join(dialect: str, Bifrost: Type[Bifrost]):
    query = """
WITH director AS (
        SELECT crew.person_id
        FROM crew
        INNER JOIN movies ON movies.id = crew.movie_id
        WHERE crew.job = 'Director' AND similarity(movies.title, 'Toy Story') > 0.5
)
SELECT
        DISTINCT movies.title,
        people."name" as director_name,
        SUBSTRING(movies.description FROM 1 FOR 100) as truncated_description
FROM
        movies
        INNER JOIN crew ON movies.id = crew.movie_id
        INNER JOIN people ON crew.person_id = people.id
        INNER JOIN director ON crew.person_id = director.person_id
WHERE
    crew.job = 'Director'
    AND movies.budget IS NOT NULL
    AND movies.revenue IS NOT NULL
    AND movies.budget >= 1000
    AND similarity(movies.title, 'Toy Story') <= 0.5;
"""  # noqa
    raise NotImplementedError
