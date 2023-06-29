from typing import Optional

import lark

from heimdallm.support.github import make_ambiguous_parse_issue

from .utils import FqColumn, JoinCondition, RequiredConstraint


class BaseException(Exception):
    """a convenience class for all heimdallm sql exceptions, to make all of them
    easier to catch"""


class GeneralParseError(BaseException):
    """thrown from our grammar parser for anything that we want to bubble up as an
    InvalidQuery exception, but we don't have access to the raw input from within the
    parser"""


class InvalidQuery(BaseException):
    """thrown when our grammar cannot parse the LLM output"""

    def __init__(self, *, query: str):
        super().__init__(f"\n\n{query}\n")
        self.query = query


class ReservedKeyword(BaseException):
    def __init__(self, *, keyword: str):
        super().__init__(f"Alias `{keyword}` is a reserved keyword")
        self.keyword = keyword


class AmbiguousParse(BaseException):
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
    """thrown when a column isn't fully qualified with the table prefix"""

    def __init__(self, column: Optional[str] = None):
        message = "Fully-qualified column name needs to be in the form 'table.column'"
        if column is not None:
            message += f" (got {column!r})"

        super().__init__(message)
        self.column = column


class IllegalSelectedColumn(BaseException):
    def __init__(self, *, column: str):
        """
        :param column: The column that was selected. This is not a FqColumn because we
        may not always have a table name.
        """
        message = f"Column `{column}` is not allowed in SELECT"
        super().__init__(message)
        self.column = column


class IllegalConditionColumn(BaseException):
    def __init__(self, *, column: FqColumn):
        message = f"Column `{column}` is not allowed in WHERE"
        super().__init__(message)
        self.column = column


class MissingRequiredConstraint(BaseException):
    def __init__(self, *, column: FqColumn, placeholder: str):
        message = f"Missing required constraint `{column}`=:{placeholder}"
        super().__init__(message)
        self.column = column
        self.placeholder = placeholder


class MissingRequiredIdentity(BaseException):
    def __init__(self, *, identities: set[RequiredConstraint]):
        message = f"Missing one required identities: {identities!r}"
        super().__init__(message)
        self.identities = identities


class IllegalJoinCondition(BaseException):
    def __init__(self, message, *, table, condition):
        super().__init__(message)
        self.table = table
        self.condition = condition


class IllegalJoinTable(BaseException):
    def __init__(self, *, join: JoinCondition):
        message = f"Join condition {join} is not allowed"
        super().__init__(message)
        self.join = join


class IllegalJoinType(BaseException):
    def __init__(self, *, join_type: str):
        message = f"JOIN type `{join_type}` is not allowed"
        super().__init__(message)
        self.join_type = join_type


class DisconnectedTable(BaseException):
    def __init__(self, *, table):
        message = f"Table `{table}` is not connected to the query"
        super().__init__(message)
        self.table = table


class BogusJoinedTable(BaseException):
    def __init__(self, *, table):
        message = f"Join condition for `{table}` does not reference the table"
        super().__init__(message)
        self.table = table


class TooManyRows(BaseException):
    def __init__(self, *, limit):
        message = f"Attempting to return too many rows ({limit})"
        super().__init__(message)
        self.limit = limit


class IllegalFunction(BaseException):
    def __init__(self, *, function):
        message = f"Function `{function}` is not allowed"
        super().__init__(message)
        self.function = function
