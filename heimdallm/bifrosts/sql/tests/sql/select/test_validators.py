from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
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


@dialects()
def test_all_fail(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.validation_only([Fail1(), Fail2()])

    query = """
    select t1.col from t1
    where
        t1.foo='bar'
    """
    with pytest.raises(exc.IllegalConditionColumn) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.foo"


@dialects()
def test_all_fail_order(dialect: str, Bifrost: Type[Bifrost]):
    """we always raise the last error, switching the validators proves this."""
    bifrost = Bifrost.validation_only([Fail2(), Fail1()])

    query = """
    select t1.col from t1
    where
        t1.foo='bar'
    """
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)
    assert e.value.column == "t1.col"


@dialects()
def test_one_succeed(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.validation_only([Fail1(), Succeed1()])

    query = """
    select t1.col from t1
    where
        t1.foo='bar'
    """
    bifrost.traverse(query)


@dialects()
def test_both_succeed(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.validation_only([Succeed1(), Succeed2()])

    query = """
    select t1.col from t1
    where
        t1.foo='bar'
    """
    bifrost.traverse(query)
