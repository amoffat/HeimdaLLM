from typing import Sequence

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn, JoinCondition, RequiredConstraint
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import PermissiveConstraints


def test_aliased_select_column():
    """tests that we can select a column from a table that was aliased via a
    join"""
    query = """
    select thing.col from t1
    join t2 thing on t1.jid = t2.jid
    """

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t2.col"}

    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query)


def test_unqualified_columns():
    query = "select col from t1"

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.UnqualifiedColumn) as e:
        bifrost.traverse(query)
    assert e.value.column == "col"


def test_unqualified_where_column():
    """a column alias in the where class is valid, as long as the alias points to an
    actual aliased column. if it doesn't, we consider it unqualified."""
    query = """
SELECT payment_id,customer_id,staff_id,rental_id,amount,payment_date
FROM payment
WHERE customer_id=:customer_id
ORDER BY payment_date DESC
LIMIT 5;
    """

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.UnqualifiedColumn) as e:
        bifrost.traverse(query)
    assert e.value.column == "customer_id"


@pytest.mark.parametrize(
    "query",
    (
        'select "t1"."col" from t1',
        'select t1.col from "t1"',
        'select t1.col from t1 where t1."id"=1',
        'select t1.col from t1 join "t2" on t1.jid = "t2".jid',
    ),
)
def test_escapes(query):
    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn):
            return column.name in {"t1.col"}

        def condition_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.id", "t2.jid", "t1.jid"}

    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query)


def test_disallowed_select_column():
    """tests that our constraint validator works when trying to select a
    column"""
    query = "select t1.col from t1"

    class AllowColumnConstraints(PermissiveConstraints):
        def select_column_allowed(self, fq_column: FqColumn) -> bool:
            return fq_column.name in {"t1.col"}

    class DenyColumnConstraints(PermissiveConstraints):
        def select_column_allowed(self, fq_column: FqColumn) -> bool:
            return fq_column.name in {"t2.col"}

    bifrost = Bifrost.mocked(AllowColumnConstraints())
    bifrost.traverse(query)

    bifrost = Bifrost.mocked(DenyColumnConstraints())
    with pytest.raises(exc.IllegalSelectedColumn) as excinfo:
        bifrost.traverse(query)

    e = excinfo.value
    assert e.column == "t1.col"


def test_required_constraint():
    """tests that our required constraint restricts the query correctly"""

    # missing constraint
    query = "select t1.col from t1"

    class RequiredConstraints(PermissiveConstraints):
        def required_constraints(self):
            return [
                RequiredConstraint(
                    column="t1.id",
                    placeholder="id",
                )
            ]

    bifrost = Bifrost.mocked(RequiredConstraints())
    with pytest.raises(exc.MissingRequiredConstraint) as excinfo:
        bifrost.traverse(query)

    e = excinfo.value
    assert e.column.name == "t1.id"
    assert e.placeholder == "id"

    # same query, but with constraint
    query = "select t1.col from t1 where t1.id=:id"
    bifrost.traverse(query)

    # same query, but with aliased table
    query = "select t1.col from t1 as aliased where aliased.id=:id"
    bifrost.traverse(query)

    # same query, without a fully qualified constraint, which would be
    # impossible for us to trace back to the original table
    query = "select t1.col from t1 as aliased where id=:id"
    with pytest.raises(exc.UnqualifiedColumn):
        bifrost.traverse(query)


@pytest.mark.parametrize(
    "query",
    (
        "select t1.col from",  # unexpected EOF
        "select `` fro t1",  # just broken
    ),
)
def test_broken_query(query):
    """tests that we raise an exception when we cannot parse the query"""

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.InvalidQuery):
        bifrost.traverse(query)


def test_select_column_arith():
    query = "select t1.col + 1 as plus_one from t1"
    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)


@pytest.mark.parametrize(
    "query",
    (
        "select 1+1 as two from t1",
        "select t1.id, (1 + 1) as two from t1",
    ),
)
def test_select_expr(query):
    """select a non-column expression"""
    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)


def test_conflicting_validations():
    query = "select t1.col from t1"

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.col"}

        def allowed_joins(self) -> Sequence[JoinCondition]:
            return []

    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query)


def test_count_disallowed_column():
    """we're allowed to count a disallowed column"""

    class GeneralConstraints(PermissiveConstraints):
        def select_column_allowed(self, fq_column: FqColumn) -> bool:
            return fq_column.name != "film_actor.film_id"

    bifrost = Bifrost.mocked(GeneralConstraints())

    # a query that uses the disallowed column in a count is allowed
    query = """
SELECT
    actor.actor_id,
    actor.first_name,
    actor.last_name,
    COUNT(film_actor.film_id)
FROM actor
JOIN film_actor ON actor.actor_id = film_actor.actor_id
GROUP BY actor.actor_id
    """

    bifrost.traverse(query, autofix=False)

    # prove that the column isn't stripped by the reconstructor
    fixed = bifrost.traverse(query, autofix=True)
    assert "film_actor.film_id" in fixed

    # but a query that uses the disallowed column without a count is not allowed
    query = """
SELECT
    actor.actor_id,
    actor.first_name,
    actor.last_name,
    film_actor.film_id
FROM actor
JOIN film_actor ON actor.actor_id = film_actor.actor_id
    """

    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query, autofix=False)
        assert e.value.column == "film_actor.film_id"

    fixed = bifrost.traverse(query, autofix=True)
    assert "film_actor.film_id" not in fixed