from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
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
    bifrost = Bifrost.mocked(PermissiveConstraints())

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
"""
    bifrost.traverse(query)


@dialects()
def test_cte_joins_separate(dialect: str, Bifrost: Type[Bifrost]):
    """Joins that happen in a CTE are counted when determining JOIN connectivity"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
WITH cta_table as (
    select t1.col from t1
    join t2 on t1.id = t2.t1_id
)
select cta_table.col from cta_table
"""

    bifrost.traverse(query)


@dialects()
def test_cte_parameterized_comparison(dialect: str, Bifrost: Type[Bifrost]):
    """Parameterized comparisons must exist outside of the CTE"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
WITH cta_table as (
    select t1.col from t1
    join t2 on t1.id = t2.t1_id
)
select cta_table.col from cta_table
"""

    bifrost.traverse(query)
