from typing import Sequence

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import RequiredConstraint
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import PermissiveConstraints


class MyConstraints(PermissiveConstraints):
    def required_constraints(self) -> Sequence[RequiredConstraint]:
        return [RequiredConstraint(column="t1.email", placeholder="email")]


def test_required_constraint():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col from t1
    """
    with pytest.raises(exc.MissingRequiredConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # required constraint, but wrong placeholder
    query = """
    select t1.col from t1
    where t1.email=:thing
    """
    with pytest.raises(exc.MissingRequiredConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # right placeholder, wrong constraint
    query = """
    select t1.col from t1
    where t1.username=:email
    """
    with pytest.raises(exc.MissingRequiredConstraint) as e:
        bifrost.traverse(query)
    assert e.value.column.name == "t1.email"

    # required constraint
    query = """
    select t1.col from t1
    where t1.email=:email
    """
    bifrost.traverse(query)


def test_required_constraint_alias():
    bifrost = Bifrost.mocked(MyConstraints())

    query = """
    select t1.col, t1.email email from t1
    where email=:email
    """
    bifrost.traverse(query)
