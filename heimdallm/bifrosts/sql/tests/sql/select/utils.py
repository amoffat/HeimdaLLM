from typing import Sequence

from heimdallm.bifrosts.sql.common import (
    ANY_JOIN,
    FqColumn,
    JoinCondition,
    ParameterizedConstraint,
)
from heimdallm.bifrosts.sql.validator import ConstraintValidator


class PermissiveConstraints(ConstraintValidator):
    """allows basically anything in the query"""

    def requester_identities(self) -> Sequence[ParameterizedConstraint]:
        return []

    def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
        return []

    def select_column_allowed(self, column: FqColumn) -> bool:
        return True

    def allowed_joins(self) -> Sequence[JoinCondition]:
        return [ANY_JOIN]

    def max_limit(self):
        return None

    def can_use_function(self, function):
        return True

    def condition_column_allowed(self, column: FqColumn) -> bool:
        return self.select_column_allowed(column)


class CustomerConstraints(PermissiveConstraints):
    def requester_identities(self):
        return [
            ParameterizedConstraint(
                column="Customer.CustomerId",
                placeholder="customer_id",
            ),
            ParameterizedConstraint(
                column="Invoice.CustomerId",
                placeholder="customer_id",
            ),
        ]

    def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
        return []
