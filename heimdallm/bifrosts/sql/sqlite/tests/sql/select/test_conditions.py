from typing import Sequence

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn, JoinCondition
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import PermissiveConstraints


class MyConstraints(PermissiveConstraints):
    def allowed_joins(self) -> Sequence[JoinCondition]:
        return [JoinCondition("t1.id", "t2.t1_id")]

    def condition_column_allowed(self, column: FqColumn) -> bool:
        return column.name in {"t1.name", "t1.thing"}


def test_allowed_where():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col from t1
    where
        t1.name='foo'
        and t1.thing='bar'
        or t1.other='baz'
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.other"

    # same query, but without the disallowed column
    query = """
    select t1.col from t1
    where
        t1.name='foo'
        and t1.thing='bar'
    """
    bifrost.traverse(query)


def test_allowed_join():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col from t1
    join t2 on t2.t1_id=t1.id and t2.other='baz'
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t2.other"

    # same query, but without the disallowed column
    query = """
    select t1.col from t1
    join t2 on t2.t1_id=t1.id
    """
    bifrost.traverse(query)


def test_allowed_having():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.name as name, sum(t1.amount) total from t1
    group by name
    having total > 100
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.amount"

    query = """
    select t1.name as name, sum(t1.thing) total from t1
    group by name
    having total > 100
    """
    bifrost.traverse(query)


def test_allowed_order_by():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.id from t1
    order by t1.amount
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.amount"

    query = """
    select t1.id from t1
    order by t1.name
    """
    bifrost.traverse(query)
