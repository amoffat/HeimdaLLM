from typing import TYPE_CHECKING, Optional

import lark

from heimdallm.context import TraverseContext
from heimdallm.support.github import make_ambiguous_parse_issue

from .common import JoinCondition, ParameterizedConstraint

if TYPE_CHECKING:
    from .common import FqColumn


class BaseException(Exception):
    """This is a convenience base class for all HeimdaLLM SQL exceptions to them easier
    to catch.

    :param ctx: The context of the Bifrost traversal.

    :meta private:
    """

    def __init__(self, msg: str, *, ctx: TraverseContext):
        self.ctx = ctx
        super().__init__(msg)


class InvalidQuery(BaseException):
    """
    Thrown when our grammar cannot parse the unwrapped LLM output.

    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, ctx: TraverseContext):
        super().__init__("Query is not valid", ctx=ctx)


class UnsupportedQuery(BaseException):
    """
    A query may be valid, but not yet supported by our parser.

    :param msg: The reason why it is unsupported.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, msg: str, ctx: TraverseContext):
        super().__init__(f"Query is not supported. Reason: {msg}", ctx=ctx)


class ReservedKeyword(BaseException):
    """
    Thrown when a the query attempts to use a reserved keyword, unescaped, as an alias
    for a table or column.

    :param keyword: The reserved keyword that was used as an alias.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, keyword: str, ctx: TraverseContext):
        super().__init__(f"Alias `{keyword}` is a reserved keyword", ctx=ctx)
        self.keyword = keyword


class AmbiguousParse(BaseException):
    """
    Thrown when our grammar parses the unwrapped LLM output, but the query results in
    multiple parse trees unexpectedly. This is a bug in our grammar, and it should be
    reported to the author via the link in the exception's output.

    :param trees: The list of parse trees that were generated from parsing the query.
    :param query: The query that was attempted to be parsed.
    :param ctx: The context of the Bifrost traversal.
    :ivar issue_link: A link to the GitHub issue that should be opened to report this.
    """

    def __init__(self, *, trees: list[lark.ParseTree], ctx: TraverseContext):
        self.issue_link = make_ambiguous_parse_issue(ctx, trees)

        super().__init__(
            f"Query resulted in {len(trees)} ambiguous parse trees. "
            "Please report this query to the HeimdaLLM maintainer using "
            f"the following link:\n{self.issue_link}",
            ctx=ctx,
        )
        self.trees = trees


class UnqualifiedColumn(BaseException):
    """
    Thrown when a column isn't fully qualified in the form ``table.column``.

    :param column: The column that was not fully qualified.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, column: str, ctx: TraverseContext):
        message = "Fully-qualified column name needs to be in the form 'table.column'"
        if column is not None:
            message += f" (got {column!r})"

        super().__init__(message, ctx=ctx)
        self.column = column


class IllegalSelectedColumn(BaseException):
    """
    Thrown when a column is selected that is not allowed by the constraint validator and
    it was not automatically removed because :doc:`/reconstruction` is disabled.

    :param column: The column that was selected. This is not a :class:`FqColumn
        <heimdallm.bifrosts.sql.common.FqColumn>` because we may not always have a table
        name.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, column: str, ctx: TraverseContext):
        message = f"Column `{column}` is not allowed in SELECT"
        super().__init__(message, ctx=ctx)
        self.column = column


class IllegalConditionColumn(BaseException):
    """
    Thrown when a column is used in a ``JOIN`` condition or a ``WHERE`` condition that
    is not allowed by the constraint validator.

    :param column: The column that was used in the condition.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, column: "FqColumn", ctx: TraverseContext):
        message = f"Column `{column}` is not allowed in WHERE"
        super().__init__(message, ctx=ctx)
        self.column = column


class MissingParameterizedConstraint(BaseException):
    """
    Thrown when a parameterized constraint is missing from the query.

    :param column: The column that is missing the constraint.
    :param placeholder: The name of the parameter placeholder for the constraint.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, column: "FqColumn", placeholder: str, ctx: TraverseContext):
        message = f"Missing required constraint `{column}`=:{placeholder}"
        super().__init__(message, ctx=ctx)
        self.column = column
        self.placeholder = placeholder


class MissingRequiredIdentity(BaseException):
    """
    Thrown when a query is missing a required requester identity.

    :param identities: The set of identities that are missing.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(
        self,
        *,
        identities: set[ParameterizedConstraint],
        ctx: TraverseContext,
    ):
        message = f"Missing one required identities: {identities!r}"
        super().__init__(message, ctx=ctx)
        self.identities = identities


class IllegalJoinTable(BaseException):
    """
    Thrown when a join spec is not allowed by the constraint validator.

    :param join: The join spec that was not allowed.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, join: JoinCondition, ctx: TraverseContext):
        message = f"Join condition {join} is not allowed"
        super().__init__(message, ctx=ctx)
        self.join = join


class IllegalJoinType(BaseException):
    """
    Thrown when a non-inner JOIN type is found.

    :param join_type: The type of JOIN that was found. This name comes directly from the
        grammar rule that captured it.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, join_type: str, ctx: TraverseContext):
        message = f"JOIN type `{join_type}` is not allowed"
        super().__init__(message, ctx=ctx)
        self.join_type = join_type


class DisconnectedTable(BaseException):
    """
    Thrown when a table has joins, but the table in the ``FROM`` clause is not connected
    to any of those joins.

    :param table: The table that is not connected to a join.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, table: str, ctx: TraverseContext):
        message = f"Table `{table}` is not connected to the query"
        super().__init__(message, ctx=ctx)
        self.table = table


class BogusJoinedTable(BaseException):
    """
    Thrown when a table's join condition does not include the table itself.

    :param table: The table that is not referenced in its own join condition.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, table: str, ctx: TraverseContext):
        message = f"Join condition for `{table}` does not reference the table"
        super().__init__(message, ctx=ctx)
        self.table = table


class TooManyRows(BaseException):
    """
    Thrown when a query returns too many rows and :doc:`/reconstruction` is disabled.

    :param limit: The number of rows that the query wants to return. Nullable if no
        limit is specified.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, limit: Optional[int], ctx: TraverseContext):
        nice_limit = limit if limit is not None else "unlimited"
        message = f"Attempting to return too many rows ({nice_limit})"
        super().__init__(message, ctx=ctx)
        self.limit = limit


class IllegalFunction(BaseException):
    """
    Thrown when a disallowed SQL function has been used in the query.

    :param function: The lowercase name of the disallowed function.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, function, ctx: TraverseContext):
        message = f"Function `{function}` is not allowed"
        super().__init__(message, ctx=ctx)
        self.function = function


class AliasConflict(BaseException):
    """
    Thrown when an alias shadows a table name or another alias name.

    :param alias: The alias that conflicts with another name.
    :param ctx: The context of the Bifrost traversal.
    """

    def __init__(self, *, alias: str, ctx: TraverseContext):
        message = f"Alias `{alias}` conflicts with a table name or another alias"
        super().__init__(message, ctx=ctx)
        self.alias = alias
