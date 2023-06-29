from typing import Any, Optional, Sequence

from . import exc


class RequiredConstraint:
    """represents a constraint that must be applied to the query. in the query,
    this comes in the form of "table.column=:placeholder". enforced by the
    grammar, the comparison is always equality, the left hand side is always a
    fully-qualified column, and the right hand side is always a placeholder.
    this requirements ensure that the query is always constrained by a value
    that the developer specifies at query execution time."""

    def __init__(self, *, column: str, placeholder: str):
        self.fq_column = FqColumn.from_string(column)
        self.placeholder = placeholder

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, RequiredConstraint)
            and other.fq_column == self.fq_column
            and other.placeholder == self.placeholder
        )

    def __hash__(self):
        return hash((self.fq_column, self.placeholder))

    def __str__(self):
        return f"{self.fq_column}=:{self.placeholder}"

    __repr__ = __str__


class FqColumn:
    """represents a fully-qualified column name. we require that LLM-produced
    queries use fully-qualified columns in their SELECT and WHERE clauses,
    otherwise we would need to infer which table owned the column, which
    requires runtime database analysis. much easier to require the LLM give us
    fully-qualified names"""

    __slots__ = ("table", "column")

    @classmethod
    def from_string(cls, s: str):
        if "." not in s:
            raise exc.UnqualifiedColumn(s)
        table, column = s.split(".")
        return cls(table=table, column=column)

    def __init__(self, *, table: str, column: str):
        self.table = table
        self.column = column

    def __str__(self):
        return f"{self.table}.{self.column}"

    name = property(str)

    def __iter__(self):
        return iter((self.table, self.column))

    def __hash__(self):
        return hash((self.table, self.column))

    def __eq__(self, other):
        return self.table == other.table and self.column == other.column

    def __repr__(self):
        return f"{self.table}.{self.column}"


class JoinCondition:
    """represents an equi-join between two tables. for our hash and equality
    functions, we don't care about the order of the join condition"""

    __slots__ = ("first", "second", "identity_placeholder")

    def __init__(self, first: str, second: str, *, identity: Optional[str] = None):
        """if identity is True, then either column in the join condition is a
        valid requester identity. this means it can be used to constrain the
        query in the same way SQLConstraintValidator.requester_identities
        does."""
        self.first = FqColumn.from_string(first)
        self.second = FqColumn.from_string(second)
        self.identity_placeholder = identity

    @property
    def requester_identities(self) -> Sequence[RequiredConstraint]:
        """if this join condition has been marked as an identity join,
        construct the required constraints for both sides of the join. we'll use
        those constraints when testing for the requester's identity"""
        if self.identity_placeholder:
            return [
                RequiredConstraint(
                    column=self.first.name,
                    placeholder=self.identity_placeholder,
                ),
                RequiredConstraint(
                    column=self.second.name,
                    placeholder=self.identity_placeholder,
                ),
            ]
        else:
            return []

    def __hash__(self):
        # it shouldn't matter which order the join condition comes in, the hash
        # should be the same
        return hash((self.first, self.second)) ^ hash((self.second, self.first))

    def __eq__(self, other):
        return (self.first == other.first and self.second == other.second) or (
            self.first == other.second and self.second == other.first
        )

    def __str__(self) -> str:
        return f"{self.first}={self.second}"

    __repr__ = __str__


class _AnyJoinCondition(JoinCondition):
    """a convenience class for representing any valid join condition."""

    def __init__(self):
        super().__init__("*.*", "*.*")


ANY_JOIN = _AnyJoinCondition()
