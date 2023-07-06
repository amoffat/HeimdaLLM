from typing import Sequence

from heimdallm.bifrosts.sql.utils import (
    ANY_JOIN,
    FqColumn,
    JoinCondition,
    RequiredConstraint,
)
from heimdallm.bifrosts.sql.validator import ConstraintValidator


class PermissiveConstraints(ConstraintValidator):
    """allows basically anything in the query"""

    def requester_identities(self):
        return []

    def required_constraints(self) -> Sequence[RequiredConstraint]:
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
        return True


class CustomerConstraints(PermissiveConstraints):
    def requester_identities(self):
        return [
            RequiredConstraint(
                column="Customer.CustomerId",
                placeholder="customer_id",
            ),
            RequiredConstraint(
                column="Invoice.CustomerId",
                placeholder="customer_id",
            ),
        ]

    def required_constraints(self) -> Sequence[RequiredConstraint]:
        return []
