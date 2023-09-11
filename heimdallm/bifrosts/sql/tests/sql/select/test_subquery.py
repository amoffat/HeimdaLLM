from typing import Sequence, Type

import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.bifrost import Bifrost
from heimdallm.bifrosts.sql.common import FqColumn, ParameterizedConstraint

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_where_in(dialect: str, Bifrost: Type[Bifrost]):
    """A subquery's selected columns are subject to the constraint validator"""

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
    bifrost = Bifrost.validation_only(Conservative())
    with pytest.raises(exc.IllegalSelectedColumn) as e:
        bifrost.traverse(query)
    assert e.value.column == "t1.id"

    class Liberal(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.col", "t1.id"}

    bifrost = Bifrost.validation_only(Liberal())
    bifrost.traverse(query)


@dialects()
def test_subquery_bad_limit(dialect: str, Bifrost: Type[Bifrost]):
    """A subquery does not require a limit"""

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
    bifrost = Bifrost.validation_only(MyConstraints())
    bifrost.traverse(query, autofix=False)


@dialects()
def test_subquery_dont_fix_limit(dialect: str, Bifrost: Type[Bifrost]):
    """The reconstructor should NOT add a limit to a subquery"""

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
    bifrost = Bifrost.validation_only(MyConstraints())
    fixed = bifrost.traverse(query)
    # outer limit preserved
    assert "limit 5" in fixed.lower()
    # inner limit added
    assert "limit 10" not in fixed.lower()


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

    bifrost = Bifrost.validation_only(MyConstraints())
    bifrost.traverse(query)

    class NoSelectConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return False

    bifrost = Bifrost.validation_only(NoSelectConstraints())
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

    bifrost = Bifrost.validation_only(PermissiveConstraints())
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

    bifrost = Bifrost.validation_only(PermissiveConstraints())
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

    bifrost = Bifrost.validation_only(PermissiveConstraints())
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
    bifrost = Bifrost.validation_only(PermissiveConstraints())
    fixed = bifrost.traverse(query)
    assert "t2.col" in fixed.lower()
    assert "t2.col2" in fixed.lower()
    assert "t3.thing" in fixed.lower()


@dialects()
def test_subquery_parameterized_comparison(dialect: str, Bifrost: Type[Bifrost]):
    """Parameterized comparisons must exist outside of the subquery to count"""

    class MyConstraints(PermissiveConstraints):
        def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
            return [ParameterizedConstraint(column="t1.email", placeholder="email")]

    bifrost = Bifrost.validation_only(MyConstraints())

    query = """
select t.email from (
    select t1.email from t1
    where t1.email=:email
) t
"""

    with pytest.raises(exc.MissingParameterizedConstraint) as e:
        bifrost.traverse(query)
    assert e.value.placeholder == "email"
