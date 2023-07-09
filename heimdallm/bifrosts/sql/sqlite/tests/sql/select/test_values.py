from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_is_not_null(Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT film.title
FROM film
JOIN inventory ON film.film_id = inventory.film_id
JOIN rental ON inventory.inventory_id = rental.inventory_id
WHERE rental.customer_id = :customer_id
AND rental.return_date IS NOT NULL
LIMIT 20;
    """
    bifrost.traverse(query)


@dialects()
def test_is_null(Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT
    rental.return_date
FROM
    rental
    INNER JOIN customer ON rental.customer_id = customer.customer_id
WHERE
    customer.customer_id = :customer_id
    AND rental.return_date IS NULL
LIMIT 20;
    """
    bifrost.traverse(query)


@dialects()
def test_agg_function_modifier_query(Bifrost: Type[Bifrost]):
    """distinct can be added in front of an aggregate function"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT COUNT(DISTINCT film.film_id) AS family_movies_rented
FROM film
JOIN film_category ON film.film_id = film_category.film_id
JOIN category ON film_category.category_id = category.category_id
JOIN inventory ON film.film_id = inventory.film_id
JOIN rental ON inventory.inventory_id = rental.inventory_id
JOIN customer ON rental.customer_id = customer.customer_id
WHERE customer.customer_id = :customer_id
AND category.`name` = 'Family'
AND rental.return_date IS NOT NULL
LIMIT 20;
    """

    bifrost.traverse(query)
