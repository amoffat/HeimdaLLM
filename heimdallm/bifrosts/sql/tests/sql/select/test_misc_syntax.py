from typing import Type

from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects("mysql", "postgres")
def test_interval(dialect: str, Bifrost: Type[Bifrost]):
    bifrost = Bifrost.validation_only(PermissiveConstraints())

    if dialect == "mysql":
        query = """
    SELECT task_name, due_date
    FROM tasks
    WHERE due_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 7 DAY;
        """
    elif dialect == "postgres":
        query = """
    SELECT task_name, due_date
    FROM tasks
    WHERE due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days';
    """
    bifrost.traverse(query)
