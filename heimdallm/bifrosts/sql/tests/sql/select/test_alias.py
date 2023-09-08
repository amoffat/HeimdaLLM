from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_where_alias(dialect: str, Bifrost: Type[Bifrost]):
    class MyConstraints(PermissiveConstraints):
        def condition_column_allowed(self, column: FqColumn) -> bool:
            return column.name == "t1.col"

    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col as thing from t1
    where thing=42
    """
    bifrost.traverse(query)

    # same query, but the alias points to a disallowed table.column
    query = """
    select t2.col as thing from t2
    where thing=42
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t2.col"


@dialects()
def test_order_alias(dialect: str, Bifrost: Type[Bifrost]):
    class MyConstraints(PermissiveConstraints):
        def condition_column_allowed(self, column: FqColumn) -> bool:
            return column.name == "t1.col"

    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col as thing from t1
    order by thing
    """
    bifrost.traverse(query)

    # same query, but the alias points to a disallowed table.column
    query = """
    select t2.col as thing from t2
    order by thing
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t2.col"


@dialects()
def test_select_function_alias(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
    select whatever(col) from t1
    """

    with pytest.raises(exc.UnqualifiedColumn) as e:
        bifrost.traverse(query, autofix=False)
    assert e.value.column == "col"


@dialects()
def test_group_by_alias(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
    SELECT COUNT(*) num_rented_movies,
        strftime('%Y', rental.rental_date) AS rental_year
    FROM rental
    JOIN customer ON rental.customer_id = customer.customer_id
    WHERE customer.customer_id = :customer_id
    GROUP BY rental_year
    LIMIT 20;
    """
    bifrost.traverse(query)


@dialects()
def test_count_star_alias(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
SELECT f.title AS movie_title, COUNT(*) AS rental_days
FROM rental r
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film f ON i.film_id = f.film_id
WHERE r.customer_id = :customer_id
GROUP BY f.title
ORDER BY rental_days DESC
LIMIT 5;
    """

    bifrost.traverse(query)


@dialects()
def test_count_disallowed_column_alias(dialect: str, Bifrost: Type[Bifrost]):
    class GeneralConstraints(PermissiveConstraints):
        def select_column_allowed(self, fq_column: FqColumn) -> bool:
            return fq_column.name != "film_actor.film_id"

    bifrost = Bifrost.mocked(GeneralConstraints())

    query = """
SELECT
    actor.actor_id,
    actor.first_name,
    actor.last_name,
    COUNT(film_actor.film_id) as film_count
FROM actor
JOIN film_actor ON actor.actor_id = film_actor.actor_id
GROUP BY actor.actor_id
ORDER BY film_count DESC
    """
    bifrost.traverse(query, autofix=False)

    # prove that the column isn't stripped by the reconstructor
    fixed = bifrost.traverse(query, autofix=True)
    assert "film_actor.film_id" in fixed


@dialects()
def test_subquery_alias_bleed(dialect: str, Bifrost: Type[Bifrost]):
    """An inner subquery alias should not mask an outer alias."""

    class GeneralConstraints(PermissiveConstraints):
        def condition_column_allowed(self, fq_column: FqColumn) -> bool:
            return fq_column.name not in {"t1.secret"}

    bifrost = Bifrost.mocked(GeneralConstraints())

    query = """
    select
        t1.col as outer_alias,
        t1.secret as inner_alias
    from t1
    where outer_alias=(
        select t2.col as inner_alias from t2
        where inner_alias=42
    ) and inner_alias=42
    """
    with pytest.raises(exc.AliasConflict) as e:
        bifrost.traverse(query)
    assert e.value.alias == "inner_alias"


@dialects()
def test_subquery_as_alias(dialect: str, Bifrost: Type[Bifrost]):
    """A subquery can be selected as an alias, but all of the columns it references are
    going to be bound to the outer alias."""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
    select (select t1.col from t1 where t1.secret='a') as thing
    from t1
    where thing=42
    """

    bifrost.traverse(query)

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name == "t1.col"

    bifrost = Bifrost.mocked(MyConstraints())
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.secret"


@dialects()
def test_selected_table_alias(dialect: str, Bifrost: Type[Bifrost]):
    """If the selected table is aliased and the query is reconstructed to have
    authoritative column names, use the authoritative selected table name."""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
    select col
    from t1 as table_alias
    """

    fixed = bifrost.traverse(query)
    assert "t1.col" in fixed
