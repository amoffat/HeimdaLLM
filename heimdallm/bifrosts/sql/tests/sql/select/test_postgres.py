from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects("postgres")
def test_type_cast(dialect: str, Bifrost: Type[Bifrost]):
    """Prove prefix type casts are allowed"""
    bifrost = Bifrost.mocked(PermissiveConstraints())

    query = """
select col::int from t1
where col.num::float > 0.4
"""
    bifrost.traverse(query)
