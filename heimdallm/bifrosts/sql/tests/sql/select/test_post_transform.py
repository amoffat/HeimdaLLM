from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_parameterized_constraint(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
    select t1.col from t1 where t1.id=:id
    """
    trusted = bifrost.traverse(query)
    if dialect == "sqlite":
        assert ":id" in trusted
    else:
        assert "%(id)s" in trusted
