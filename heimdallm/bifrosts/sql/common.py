from typing import Any, Optional, Sequence

from . import exc


class ParameterizedConstraint:
    """This represents a constraint that *must* be applied to the query.

    In the query, this comes in the form of ``table.column=:placeholder``. Enforced by
    the grammar, the comparison is always equality, the left hand side is always a
    fully-qualified column, and the right hand side is always a placeholder. These
    requirements ensure that the query is always constrained by a value that the
    developer specifies at query execution time.

    :param column: The fully-qualified column name.
    :param placeholder: The placeholder name for the value that your database expects to
        be interpolated at execution time.
    """

    def __init__(self, *, column: str, placeholder: str):
        self.fq_column = FqColumn.from_string(column)
        self.placeholder = placeholder

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ParameterizedConstraint)
            and other.fq_column == self.fq_column
            and other.placeholder == self.placeholder
        )

    def __hash__(self):
        return hash((self.fq_column, self.placeholder))

    def __str__(self):
        return f"{self.fq_column}=:{self.placeholder}"

    __repr__ = __str__


class FqColumn:
    """This represents a fully-qualified column name.

    We require that LLM-produced queries from SQL Bifrosts use fully-qualified columns
    in their clauses, because if they didn't, we would need to infer which table owned
    the column, which requires runtime schema analysis. We could do that, but maybe in
    the future. It's much more straightforward to instruct that the LLM give us
    fully-qualified names.

    :param table: The table name.
    :param column: The column name.
    """

    __slots__ = ("table", "column")

    @classmethod
    def from_string(cls, fq_column_name: str) -> "FqColumn":
        """Parses a fully-qualified column name from a string, using the expected
        format of ``table.column``

        :param fq_column_name: The fully-qualified column name.
        :raises UnqualifiedColumn: If the string does not contain a period."""
        if "." not in fq_column_name:
            raise exc.UnqualifiedColumn(fq_column_name)
        table, column = fq_column_name.split(".")
        return cls(table=table, column=column)

    def __init__(self, *, table: str, column: str):
        self.table = table
        self.column = column

    def __str__(self):
        return f"{self.table}.{self.column}"

    @property
    def name(self) -> str:
        """A convenience property that returns the fully-qualified column name as a
        string in the same format ``table.column``"""
        return str(self)

    def __iter__(self):
        return iter((self.table, self.column))

    def __hash__(self):
        return hash((self.table, self.column))

    def __eq__(self, other):
        return self.table == other.table and self.column == other.column

    def __repr__(self):
        return f"{self.table}.{self.column}"


class JoinCondition:
    """This represents an equi-join between two tables, on two columns. The order of
    the fully-qualified columns does not matter; matching will work correctly in the
    code.

    :param first: The first fully-qualified column.
    :param second: The second fully-qualified column.
    :param identity: If the columns specified in this join condition can also be used as
        a :meth:`requester identity
        <heimdallm.bifrosts.sql.sqlite.select.validator.ConstraintValidator.requester_identities>`
        for the query, then this should be set to the name of the placeholder where the
        identity will be populated at runtime.
    """

    __slots__ = ("first", "second", "identity_placeholder")

    def __init__(self, first: str, second: str, *, identity: Optional[str] = None):
        self.first = FqColumn.from_string(first)
        self.second = FqColumn.from_string(second)
        self.identity_placeholder = identity

    @property
    def requester_identities(self) -> Sequence[ParameterizedConstraint]:
        """If this join condition has been marked as an identity join,
        construct the required constraints for both sides of the join. We'll use those
        constraints when testing for the requester's identity.

        :meta private:
        """
        if self.identity_placeholder:
            return [
                ParameterizedConstraint(
                    column=self.first.name,
                    placeholder=self.identity_placeholder,
                ),
                ParameterizedConstraint(
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
    """A convenience class for representing any valid join condition."""

    def __init__(self):
        super().__init__("*.*", "*.*")


#: A convenience object that represents any valid join condition. Only use it for a
#: validator that represents full admin access to your database.
ANY_JOIN = _AnyJoinCondition()
