from typing import Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.bifrost import Bifrost
from heimdallm.bifrosts.sql.common import FqColumn

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_where_condition(dialect: str, Bifrost: Type[Bifrost]):
    query = """
select t1.col from t1
where t1.id=(select t2.id from t2)
"""

    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)


@dialects()
def test_parameterized_constraint(dialect: str, Bifrost: Type[Bifrost]):
    query = """
select t1.col from t1
where t1.id=(select t2.id from t2)
"""

    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)


@dialects()
def test_where_in(dialect: str, Bifrost: Type[Bifrost]):
    """WHERE X IN subquery, with subquery having columns that must be allowed by the
    constraint validator"""

    class Conservative(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.col"}

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
)
    """
    bifrost = Bifrost.mocked(Conservative())
    with pytest.raises(exc.IllegalSelectedColumn):
        bifrost.traverse(query)

    class Liberal(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.col", "t1.id"}

    bifrost = Bifrost.mocked(Liberal())
    bifrost.traverse(query)


@dialects()
def test_subquery_bad_limit(dialect: str, Bifrost: Type[Bifrost]):
    """Tests that a subquery must be limited by a LIMIT clause"""

    class MyConstraints(PermissiveConstraints):
        def max_limit(self):
            return 10

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
)
limit 10
    """
    bifrost = Bifrost.mocked(MyConstraints())
    with pytest.raises(exc.TooManyRows) as e:
        bifrost.traverse(query, autofix=False)
        assert e.value.limit is None

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
    limit 11
)
limit 10
    """
    bifrost = Bifrost.mocked(MyConstraints())
    with pytest.raises(exc.TooManyRows) as e:
        bifrost.traverse(query, autofix=False)
        assert e.value.limit == 11


@dialects()
def test_subquery_good_limit(dialect: str, Bifrost: Type[Bifrost]):
    class MyConstraints(PermissiveConstraints):
        def max_limit(self):
            return 10

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
    limit 10
)
limit 10
    """
    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query, autofix=False)


@dialects()
def test_subquery_fix_limit(dialect: str, Bifrost: Type[Bifrost]):
    class MyConstraints(PermissiveConstraints):
        def max_limit(self):
            return 10

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
)
limit 5
    """
    bifrost = Bifrost.mocked(MyConstraints())
    fixed = bifrost.traverse(query)
    # outer limit preserved
    assert "limit 5" in fixed.lower()
    # inner limit added
    assert "limit 10" in fixed.lower()


@dialects()
def test_subquery_alias(dialect: str, Bifrost: Type[Bifrost]):
    """Tests that a subquery can be aliased and referenced by that alias"""

    query = """
select t1.t2col from (
    select t2.col as t2col from t2
) t1
    """

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t2.col"}

    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query)

    class NoSelectConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return False

    bifrost = Bifrost.mocked(NoSelectConstraints())
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)
        assert e.value.column == "t2.col"


@dialects()
def test_subquery_alias_conflict(dialect: str, Bifrost: Type[Bifrost]):
    """If a subquery is aliased, and that alias conflicts with a table name,
    then the query is ambiguous and should be rejected"""

    query = """
select t1.col from t1
join (
    select t2.col from t2
) as t1 on t1.id=t1.col
    """

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.AliasConflict) as e:
        bifrost.traverse(query)
        assert e.value.alias == "t1"


@dialects()
def test_subquery_alias_conflict2(dialect: str, Bifrost: Type[Bifrost]):
    """Alias conflicts anywhere in the query should be rejected"""

    query = """
select t1.col, t1.col2 as alias_col from (
    select t2.col as alias_col from t2
) as sq
    """

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.AliasConflict) as e:
        bifrost.traverse(query)
    assert e.value.alias == "alias_col"


@dialects()
def test_subquery_alias_conflict3(dialect: str, Bifrost: Type[Bifrost]):
    """Alias conflicts anywhere in the query should be rejected"""

    query = """
select t1.col from (
    select t1.col from t2 as t1
) t1
    """

    bifrost = Bifrost.mocked(PermissiveConstraints())
    with pytest.raises(exc.AliasConflict) as e:
        bifrost.traverse(query)
    assert e.value.alias == "t1"


@dialects()
def test_subquery_fq(dialect: str, Bifrost: Type[Bifrost]):
    """A subquery should be able to have its single columns fully-qualified
    automatically"""

    query = """
select t1.col, t1.col2 from (
    select col, col2 from (
        select thing from t3
    ) t2
) t1
    """
    bifrost = Bifrost.mocked(PermissiveConstraints())
    fixed = bifrost.traverse(query)
    assert "t2.col" in fixed.lower()
    assert "t2.col2" in fixed.lower()
    assert "t3.thing" in fixed.lower()
