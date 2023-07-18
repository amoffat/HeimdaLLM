from typing import Type

from heimdallm.bifrosts.sql.common import FqColumn
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from ..utils import dialects
from .utils import PermissiveConstraints


@dialects()
def test_where_eq(dialect: str, Bifrost: Type[Bifrost]):
    query = """
SELECT employees.emp_no, employees.first_name, employees.last_name
FROM dept_emp
JOIN employees ON employees.emp_no = dept_emp.emp_no
WHERE dept_emp.dept_no = (
    SELECT dept_emp.dept_no
    FROM dept_emp
    WHERE dept_emp.emp_no = :employee_id
    AND dept_emp.from_date <= FROM_UNIXTIME(:timestamp)
    AND dept_emp.to_date > FROM_UNIXTIME(:timestamp)
)
AND dept_emp.emp_no != :employee_id
AND dept_emp.from_date <= FROM_UNIXTIME(:timestamp)
AND dept_emp.to_date > FROM_UNIXTIME(:timestamp);
"""

    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)


@dialects("sqlite")
def test_where_in(dialect: str, Bifrost: Type[Bifrost]):
    """WHERE X IN subquery, with subquery having columns that must be allowed by the
    constraint validator"""

    class MyConstraints(PermissiveConstraints):
        def select_column_allowed(self, column: FqColumn) -> bool:
            return column.name in {"t1.col"}

    query = """
select t1.col from t1
where t1.id in (
    select t1.id from t1
    where t1.col='foo'
)
    """

    bifrost = Bifrost.mocked(MyConstraints())
    bifrost.traverse(query)


def test_unlimited_subquery():
    raise NotImplementedError
