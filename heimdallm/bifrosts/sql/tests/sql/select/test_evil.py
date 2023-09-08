from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import FqColumn
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_no_outer_join(dialect: str, Bifrost: Type[Bifrost]):
    """outer joins should not be allowed, because they can be used to return
    rows that are outside of the join constraint"""
    query = """
select t1.secret
from t1
left join t2 on t1.jid = t2.jid
    """

    bifrost = Bifrost.validation_only(PermissiveConstraints())
    with pytest.raises(exc.IllegalJoinType) as e:
        bifrost.traverse(query)
    assert e.value.join_type == "OUTER_JOIN"


@dialects()
def test_no_select_star(dialect: str, Bifrost: Type[Bifrost]):
    query = "select * from t1"

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return True

    bifrost = Bifrost.validation_only(MyConstraints())
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)

    assert e.value.column == "*"


@dialects()
def test_allow_count_star(dialect: str, Bifrost: Type[Bifrost]):
    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            # count(*) doesn't count as a column that needs to be allowlisted
            return False

    bifrost = Bifrost.validation_only(MyConstraints())

    query = "select count(*) from t1"
    bifrost.traverse(query)

    query = "select count(*) as num from t1"
    bifrost.traverse(query)


@dialects("sqlite")
def test_keyword_table_alias(dialect: str, Bifrost: Type[Bifrost]):
    query = """
select t1.secret
from t1 group
    """

    bifrost = Bifrost.validation_only(PermissiveConstraints())
    with pytest.raises(exc.ReservedKeyword) as e:
        bifrost.traverse(query)
    assert e.value.keyword == "group"

    # same query, but with identifier quoted
    query = """
select t1.secret
from t1 "group"
    """
    bifrost.traverse(query)


@dialects("sqlite")
def test_keyword_column_alias(dialect: str, Bifrost: Type[Bifrost]):
    query = """
select t1.secret group
from t1
    """

    bifrost = Bifrost.validation_only(PermissiveConstraints())
    with pytest.raises(exc.ReservedKeyword) as e:
        bifrost.traverse(query)
    assert e.value.keyword == "group"

    # same query, but with identifier quoted
    query = """
select t1.secret "group"
from t1
    """
    bifrost.traverse(query)


@dialects("sqlite")
def test_escaped_single_quote(dialect: str, Bifrost: Type[Bifrost]):
    query = """
select t1.col
from t1
where t1.col='let''s go'
    """
    bifrost = Bifrost.validation_only(PermissiveConstraints())
    bifrost.traverse(query)
