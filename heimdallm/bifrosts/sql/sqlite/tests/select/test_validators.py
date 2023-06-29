import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.sqlite.select.bifrost import SQLBifrost
from heimdallm.bifrosts.sql.utils import FqColumn

from .utils import PermissiveConstraints


class Fail1(PermissiveConstraints):
    def select_column_allowed(self, column: FqColumn) -> bool:
        return False


class Fail2(PermissiveConstraints):
    def condition_column_allowed(self, column: FqColumn) -> bool:
        return False


class Succeed1(PermissiveConstraints):
    def select_column_allowed(self, column: FqColumn) -> bool:
        return True


class Succeed2(PermissiveConstraints):
    def condition_column_allowed(self, column: FqColumn) -> bool:
        return True


def test_all_fail():
    bifrost = SQLBifrost.mocked([Fail1(), Fail2()])

    query = """
    select t1.col from t1
    where
        t1.name='foo'
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.name"


def test_all_fail_order():
    """we always raise the last error, switching the validators proves this."""
    bifrost = SQLBifrost.mocked([Fail2(), Fail1()])

    query = """
    select t1.col from t1
    where
        t1.name='foo'
    """
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)
    assert e.value.column == "t1.col"


def test_one_succeed():
    bifrost = SQLBifrost.mocked([Fail1(), Succeed1()])

    query = """
    select t1.col from t1
    where
        t1.name='foo'
    """
    bifrost.traverse(query)


def test_both_succeed():
    bifrost = SQLBifrost.mocked([Succeed1(), Succeed2()])

    query = """
    select t1.col from t1
    where
        t1.name='foo'
    """
    bifrost.traverse(query)
