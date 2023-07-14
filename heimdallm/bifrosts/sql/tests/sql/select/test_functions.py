from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


class MyConstraints(PermissiveConstraints):
    def can_use_function(self, fn):
        return fn != "nope"


@dialects()
def test_disallowed_in_select(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = "select yep(t1.col) from t1"
    bifrost.traverse(query)

    query = "select nope(t1.col) from t1"
    with pytest.raises(exc.IllegalFunction) as e:
        bifrost.traverse(query)
    assert e.value.function == "nope"

    query = "select yep(t1.col, yep(yep(nope()))) from t1"
    with pytest.raises(exc.IllegalFunction) as e:
        bifrost.traverse(query)
    assert e.value.function == "nope"


@dialects()
def test_disallowed_in_where(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = "select t1.col from t1 where yep(t1.col)=1"
    bifrost.traverse(query)

    query = "select t1.col from t1 where nope(t1.col)=1"
    with pytest.raises(exc.IllegalFunction) as e:
        bifrost.traverse(query)
    assert e.value.function == "nope"


@dialects()
def test_disallowed_in_join(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = "select t1.col from t1 join t2 on t1.t2_id=t2.id and t2.col=nope()"
    with pytest.raises(exc.IllegalFunction) as e:
        bifrost.traverse(query)
    assert e.value.function == "nope"


@dialects()
def test_case_insensitive(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(MyConstraints())

    query = "select YEP(t1.col) from t1"
    bifrost.traverse(query)

    query = "select NOPE(t1.col) from t1"
    with pytest.raises(exc.IllegalFunction) as e:
        bifrost.traverse(query)
    assert e.value.function == "nope"
