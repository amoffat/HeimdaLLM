from typing import Sequence, Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import ParameterizedConstraint
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


class MyConstraints(PermissiveConstraints):
    def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
        return [ParameterizedConstraint(column="t1.email", placeholder="email")]


@dialects()
def test_parameterized_constraints(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col from t1
    """
    with pytest.raises(exc.MissingParameterizedConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # required constraint, but wrong placeholder
    query = """
    select t1.col from t1
    where t1.email=:thing
    """
    with pytest.raises(exc.MissingParameterizedConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # right placeholder, wrong constraint
    query = """
    select t1.col from t1
    where t1.username=:email
    """
    with pytest.raises(exc.MissingParameterizedConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # required constraint
    query = """
    select t1.col from t1
    where t1.email=:email
    """
    bifrost.traverse(query)


@dialects()
def test_parameterized_constraint_outer_query(dialect: str, Bifrost: Type[Bifrost]):
    """only the outer query should be checked for required constraints"""

    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col from t1
    where t1.id=(
        select t1.id from t1
        where t1.email=:email
    )
    """
    with pytest.raises(exc.MissingParameterizedConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"


@dialects()
def test_parameterized_constraint_alias(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col, t1.email email from t1
    where email=:email
    """
    bifrost.traverse(query)


@dialects()
def test_backwards_placeholder(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col, t1.email email from t1
    where :email=t1.email
    """
    bifrost.traverse(query)
