from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_alter_limit(dialect: str, Bifrost: Type[Bifrost]):
    limit = 25

    class LimitConstraints(PermissiveConstraints):
        def max_limit(self):
            return limit

    bifrost = Bifrost.validation_only(LimitConstraints())
    unlimited_bifrost = Bifrost.validation_only(PermissiveConstraints())

    # no limit
    query = "select t1.col from t1"
    with pytest.raises(exc.TooManyRows) as e:
        bifrost.traverse(query, autofix=False)
    assert e.value.limit is None

    # no limit constraint, so no limit is added when "fixed"
    trusted_query = unlimited_bifrost.traverse(query)
    assert "limit" not in trusted_query.lower()

    # add limit
    trusted_query = bifrost.traverse(query)
    assert f"limit {limit}" in trusted_query.lower()

    # lower limit
    query = f"select t1.col from t1 limit {limit * 2}"
    trusted_query = bifrost.traverse(query)
    assert f"limit {limit}" in trusted_query.lower()

    # the unlimited constraints do not lower the limit
    trusted_query = unlimited_bifrost.traverse(query)
    assert f"limit {limit * 2}" in trusted_query.lower()

    # do not raise limit
    query = f"select t1.col from t1 limit {limit // 2}"
    trusted_query = bifrost.traverse(query)
    assert f"limit {limit // 2}" in trusted_query.lower()


def test_limit_preserve_offset():
    """updating a limit should not affect the offset"""
    limit = 25
    offset = 10

    class LimitConstraints(PermissiveConstraints):
        def max_limit(self):
            return limit

    bifrost = Bifrost.validation_only(LimitConstraints())
    query = f"select t1.col from t1 limit {limit *2} offset {offset}"
    trusted_query = bifrost.traverse(query)
    assert f"limit {limit}" in trusted_query.lower()
    assert f"offset {offset}" in trusted_query.lower()


@dialects("sqlite")
def test_good_formatting(dialect: str, Bifrost: Type[Bifrost]):
    """verify that the reconstructed query has decent formatting. doesn't have to match
    the original, just look good enough and be semantically the same"""
    bifrost = Bifrost.validation_only(PermissiveConstraints())

    query = """
SELECT f.title,f.rating, f.release_year
FROM film f
INNER JOIN inventory i ON f.film_id = i.film_id
INNER JOIN rental r ON i.inventory_id = r.inventory_id
INNER JOIN customer c ON r.customer_id = c.customer_id
WHERE c.customer_id = :customer_id
AND (f.rating = 'R' OR f.rating = 'NC-17')
AND f.release_year IS NOT NULL
ORDER BY f.release_year DESC
LIMIT 20;
"""
    trusted_query = bifrost.traverse(query)

    correct = """SELECT f.title,f.rating,f.release_year FROM film as f INNER JOIN inventory as i on f.film_id=i.film_id INNER JOIN rental as r on i.inventory_id=r.inventory_id INNER JOIN customer as c on r.customer_id=c.customer_id WHERE c.customer_id=:customer_id AND (f.rating='R' OR f.rating='NC-17') AND f.release_year IS NOT NULL ORDER BY f.release_year DESC LIMIT 20;"""  # noqa: E501
    assert correct == trusted_query


@dialects("sqlite")
def test_remove_illegal_columns(dialect: str, Bifrost: Type[Bifrost], conn):
    """show that we can automatically filter out illegal columns"""

    class MyConstraints(PermissiveConstraints):
        def condition_column_allowed(self, column: FqColumn) -> bool:
            return True

        def select_column_allowed(self, column: FqColumn) -> bool:
            return not column.name.endswith("_id")

    bifrost = Bifrost.validation_only(MyConstraints())

    query = """
SELECT f.film_id, f.title, f.description, f.release_year, f.language_id, r.rental_date,
    s.address_id
FROM film f
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
JOIN store s ON i.store_id = s.store_id
JOIN customer c ON r.customer_id = c.customer_id
WHERE c.customer_id = :customer_id
    """

    trusted_query = bifrost.traverse(query)

    cur = conn.cursor()
    cur.execute(trusted_query, {"customer_id": 148})
    columns = [desc[0] for desc in cur.description]
    assert columns == ["title", "description", "release_year", "rental_date"]


@pytest.mark.skip("TODO")
@dialects()
def test_leave_illegal_columns(dialect: str, Bifrost: Type[Bifrost]):
    """columns referenced in an aggregate function should not be removed, since they
    don't reveal information"""

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return not column.name.endswith("_id")

    bifrost = Bifrost.validation_only(MyConstraints())

    query = """
SELECT film.film_id, film.title, COUNT(rental.rental_id) AS rental_count
FROM film
INNER JOIN inventory ON inventory.film_id = film.film_id
INNER JOIN rental ON rental.inventory_id = inventory.inventory_id
WHERE rental.customer_id = :customer_id
GROUP BY film.film_id, film.title
ORDER BY rental_count DESC
LIMIT 10;
"""

    bifrost.traverse(query, autofix=False)


@dialects()
def test_unqualified_columns(dialect: str, Bifrost: Type[Bifrost]):
    """an unqualified column should be qualified with the table name from the select"""
    bifrost = Bifrost.validation_only(PermissiveConstraints())

    query = """
SELECT salary
FROM salaries
WHERE emp_no = :employee_id
AND from_date <= DATE(:timestamp)
AND to_date >= DATE(:timestamp)
"""

    trusted_query = bifrost.traverse(query)
    assert "salaries.salary" in trusted_query


@pytest.mark.skip("TODO")
@dialects()
def test_add_parameterized_constraints(dialect: str, Bifrost: Type[Bifrost]):
    """show that we can add a parameterized_constraint to a query"""
    raise NotImplementedError
