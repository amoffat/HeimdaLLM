from typing import TYPE_CHECKING, Optional

import lark

from heimdallm.support.github import make_ambiguous_parse_issue

if TYPE_CHECKING:
    from .common import FqColumn, JoinCondition, RequiredConstraint


class BaseException(Exception):
    """This is a convenience base class for all HeimdaLLM SQL exceptions to them easier
    to catch.

    :meta private:
    """


class GeneralParseError(BaseException):
    """
    Thrown from our grammar parser for anything that we want to bubble up as an
    InvalidQuery exception, but we don't have access to the raw input from within the
    parser
    """


class InvalidQuery(BaseException):
    """
    Thrown when our grammar cannot parse the unwrapped LLM output.

    :param query: The query that was attempted to be parsed.
    """

    def __init__(self, *, query: str):
        super().__init__(f"\n\n{query}\n")
        self.query = query


class ReservedKeyword(BaseException):
    """
    Thrown when a the query attempts to use a reserved keyword, unescaped, as an alias
    for a table or column.

    :param keyword: The reserved keyword that was used as an alias.
    """

    def __init__(self, *, keyword: str):
        super().__init__(f"Alias `{keyword}` is a reserved keyword")
        self.keyword = keyword


class AmbiguousParse(BaseException):
    """
    Thrown when our grammar parses the unwrapped LLM output, but the query results in
    multiple parse trees unexpectedly. This is a bug in our grammar, and it should be
    reported to the author via the link in the exception's output.

    :param trees: The list of parse trees that were generated from parsing the query.
    :param query: The query that was attempted to be parsed.
    :ivar issue_link: A link to the GitHub issue that should be opened to report this.
    """

    def __init__(self, *, trees: list[lark.ParseTree], query: str):
        self.issue_link = make_ambiguous_parse_issue(query, trees)

        super().__init__(
            f"Query resulted in {len(trees)} ambiguous parse trees. "
            "Please report this query to the HeimdaLLM maintainer using "
            f"the following link:\n{self.issue_link}"
        )
        self.trees = trees
        self.query = query


class UnqualifiedColumn(BaseException):
    """
    Thrown when a column isn't fully qualified in the form ``table.column``.

    :param column: The column that was not fully qualified.
    """

    def __init__(self, column: str):
        message = "Fully-qualified column name needs to be in the form 'table.column'"
        if column is not None:
            message += f" (got {column!r})"

        super().__init__(message)
        self.column = column


class IllegalSelectedColumn(BaseException):
    """
    Thrown when a column is selected that is not allowed by the constraint validator and
    it was not automatically removed because :doc:`/reconstruction` is disabled.

    :param column: The column that was selected. This is not a :class:`FqColumn
        <heimdallm.bifrosts.sql.common.FqColumn>` because we may not always have a table
        name.
    """

    def __init__(self, *, column: str):
        message = f"Column `{column}` is not allowed in SELECT"
        super().__init__(message)
        self.column = column


class IllegalConditionColumn(BaseException):
    """
    Thrown when a column is used in a ``JOIN`` condition or a ``WHERE`` condition that
    is not allowed by the constraint validator.

    :param column: The column that was used in the condition.
    """

    def __init__(self, *, column: "FqColumn"):
        message = f"Column `{column}` is not allowed in WHERE"
        super().__init__(message)
        self.column = column


class MissingRequiredConstraint(BaseException):
    def __init__(self, *, column: "FqColumn", placeholder: str):
        message = f"Missing required constraint `{column}`=:{placeholder}"
        super().__init__(message)
        self.column = column
        self.placeholder = placeholder


class MissingRequiredIdentity(BaseException):
    def __init__(self, *, identities: set["RequiredConstraint"]):
        message = f"Missing one required identities: {identities!r}"
        super().__init__(message)
        self.identities = identities


class IllegalJoinTable(BaseException):
    """
    Thrown when a join spec is not allowed by the constraint validator.

    :param join: The join spec that was not allowed.
    """

    def __init__(self, *, join: "JoinCondition"):
        message = f"Join condition {join} is not allowed"
        super().__init__(message)
        self.join = join


class IllegalJoinType(BaseException):
    """
    Thrown when a non-inner JOIN type is found.

    :param join_type: The type of JOIN that was found. This name comes directly from the
        grammar rule that captured it.
    """

    def __init__(self, *, join_type: str):
        message = f"JOIN type `{join_type}` is not allowed"
        super().__init__(message)
        self.join_type = join_type


class DisconnectedTable(BaseException):
    """
    Thrown when a table has joins, but the table in the ``FROM`` clause is not connected
    to any of those joins.

    :param table: The table that is not connected to a join.
    """

    def __init__(self, *, table: str):
        message = f"Table `{table}` is not connected to the query"
        super().__init__(message)
        self.table = table


class BogusJoinedTable(BaseException):
    """
    Thrown when a table's join condition does not include the table itself.

    :param table: The table that is not referenced in its own join condition.
    """

    def __init__(self, *, table: str):
        message = f"Join condition for `{table}` does not reference the table"
        super().__init__(message)
        self.table = table


class TooManyRows(BaseException):
    """
    Thrown when a query returns too many rows and :doc:`/reconstruction` is disabled.

    :param limit: The number of rows that the query wants to return. Nullable if no
        limit is specified.
    """

    def __init__(self, *, limit: Optional[int]):
        nice_limit = limit if limit is not None else "unlimited"
        message = f"Attempting to return too many rows ({nice_limit})"
        super().__init__(message)
        self.limit = limit


class IllegalFunction(BaseException):
    """
    Thrown when a disallowed SQL function has been used in the query.

    :param function: The lowercase name of the disallowed function.
    """

    def __init__(self, *, function):
        message = f"Function `{function}` is not allowed"
        super().__init__(message)
        self.function = function


class AliasConflict(BaseException):
    """
    Thrown when an alias shadows a table name or another alias name.

    :param alias: The alias that conflicts with another name.
    """

    def __init__(self, *, alias: str):
        message = f"Alias `{alias}` conflicts with a table name or another alias"
        super().__init__(message)
        self.alias = alias
