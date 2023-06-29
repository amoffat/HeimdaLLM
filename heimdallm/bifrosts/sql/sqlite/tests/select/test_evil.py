import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.sqlite.select.bifrost import SQLBifrost
from heimdallm.bifrosts.sql.utils import FqColumn

from .utils import PermissiveConstraints


def test_no_outer_join():
    """outer joins should not be allowed, because they can be used to return
    rows that are outside of the join constraint"""
    query = """
select t1.secret
from t1
left join t2 on t1.jid = t2.jid
    """

    bifrost = SQLBifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.IllegalJoinType) as e:
        bifrost.traverse(query)
    assert e.value.join_type == "OUTER_JOIN"


def test_no_select_star():
    query = "select * from t1"

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return True

    bifrost = SQLBifrost.mocked(MyConstraints())
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)

    assert e.value.column == "*"


def test_allow_count_star():
    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            # count(*) doesn't count as a column that needs to be allowlisted
            return False

    bifrost = SQLBifrost.mocked(MyConstraints())

    query = "select count(*) from t1"
    bifrost.traverse(query)

    query = "select count(*) as num from t1"
    bifrost.traverse(query)


def test_keyword_table_alias():
    query = """
select t1.secret
from t1 group
    """

    bifrost = SQLBifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.ReservedKeyword) as e:
        bifrost.traverse(query)
    assert e.value.keyword == "group"

    # same query, but with identifier quoted
    query = """
select t1.secret
from t1 "group"
    """
    bifrost.traverse(query)


def test_keyword_column_alias():
    query = """
select t1.secret group
from t1
    """

    bifrost = SQLBifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.ReservedKeyword) as e:
        bifrost.traverse(query)
    assert e.value.keyword == "group"

    # same query, but with identifier quoted
    query = """
select t1.secret "group"
from t1
    """
    bifrost.traverse(query)


def test_escaped_single_quote():
    query = """
select t1.col
from t1
where t1.col='let''s go'
    """
    bifrost = SQLBifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)
