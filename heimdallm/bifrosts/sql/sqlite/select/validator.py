from abc import abstractmethod
from itertools import chain
from typing import Optional, Sequence, cast

from lark import Lark, ParseTree
from lark.exceptions import VisitError
from lark.reconstruct import Reconstructor

from heimdallm.bifrosts.sql import exc
from heimdallm.constraints import ConstraintValidator as _ConstraintValidator

from ...utils import ANY_JOIN, FqColumn, JoinCondition, RequiredConstraint
from .. import presets
from ..utils.visitors import AliasCollector
from .visitors import FacetCollector, Facets


class SQLConstraintValidator(_ConstraintValidator):
    """almost all methods are abstract because we want to force the developer
    to implement them. the cost of not implementing them by accident is high."""

    @abstractmethod
    def requester_identities(self) -> Sequence[RequiredConstraint]:
        """Returns the identity of the requester, as represented in the
        database. this is used to instruct the LLM how to constrain the query
        that it generates. only one of these identities needs to match.

        the reason that we return a sequence, and not a single identity, is that
        sometimes an LLM will specify the constraint as part of a JOIN
        condition, and not a WHERE condition. in that case, the column in the
        JOIN condition may not match the column you expect, for example,

            Invoice.CustomerId vs Customer.CustomerId

        although they represent the same identity, they are different tables and
        columns, but constraining on one of them is sufficient.
        """
        raise NotImplementedError(
            "You must explicitly provide the requester identity, "
            "or an empty list for full access (dangerous)"
        )

    @abstractmethod
    def required_constraints(self) -> Sequence[RequiredConstraint]:
        """Returns a sequence of secure constraints that must exist in the WHERE
        clause of the query"""
        raise NotImplementedError(
            "You must explicitly provide a sequence of required constraints, "
            "or an empty list for no constraints"
        )

    @abstractmethod
    def select_column_allowed(self, column: FqColumn) -> bool:
        """Ensures that the column is allowed to be selected in the `SELECT` clause"""
        return False

    @abstractmethod
    def allowed_joins(self) -> Sequence[JoinCondition]:
        """Returns all of the tables allowed to be connected to the query,
        either via a JOIN, or via a FROM. this encompasses both cases because
        LLMs frequently produce queries that select unpredictable tables with
        "FROM", even if that table is valid to be connected via "JOIN". so to
        handle this, we consider a table selected with FROM as a JOIN with no
        explicit conditions. in practice, if there are other joins in the query,
        the selected table will have an explicit condition via the ON clause. if
        there are no other joins, the selected table will have no join
        conditions.
        """
        return []

    @abstractmethod
    def max_limit(self) -> Optional[int]:
        """Return the maximum number of rows that can be returned by a query. if
        None, there is no limit."""
        return None

    def can_use_function(self, function):
        """Ensures that the function is allowed to be used in the query"""
        return function in presets.safe_functions

    def condition_column_allowed(self, fq_column: FqColumn) -> bool:
        """Checks if a column is allowed in a WHERE, JOIN, HAVING, or ORDER BY"""
        # let's default to "if you can see it, you can use it"
        return self.select_column_allowed(fq_column)

    def fix(self, grammar: Lark, tree: ParseTree) -> str:
        """A parse tree may be valid SQL, but it may not be valid according to
        the validator's constraints. we may be able to make intelligent
        decisions about those constraints, and fix the parse tree though, for
        example, by adding a limit to a query."""

        # gets around a circular import issue
        from heimdallm.bifrosts.sql.sqlite.select import reconstruct

        transform = reconstruct.ReconstructTransformer(self)
        try:
            fixed_tree = transform.transform(tree)
        except VisitError as e:
            if isinstance(e.orig_exc, exc.BaseException):
                raise e.orig_exc
            raise e

        output = Reconstructor(grammar).reconstruct(
            fixed_tree,
            postproc=reconstruct.postproc,
        )
        return output

    def validate(self, untrusted_input: str, tree: ParseTree):
        """Analyze the tree and validate it against our SQL constraints"""
        try:
            alias_collector = AliasCollector()
            alias_collector.visit(tree)

            facets = Facets()
            facet_collector = FacetCollector(facets, alias_collector)
            facet_collector.visit(tree)
        except exc.GeneralParseError:
            raise exc.InvalidQuery(query=untrusted_input)

        # check the select column allowlist
        for fq_column in facets.selected_columns:
            if not self.select_column_allowed(fq_column):
                raise exc.IllegalSelectedColumn(column=fq_column.name)

        # check the join condition allowlist
        any_join_cond_allowed = ANY_JOIN in self.allowed_joins()
        for table, join_specs in facets.joined_tables.items():
            for join_spec in join_specs:
                allowed = any_join_cond_allowed or join_spec in self.allowed_joins()
                if not allowed:
                    raise exc.IllegalJoinTable(join=join_spec)

        # ensure that the selected table is joined to another table, if joins exist
        if (
            facets.joined_tables
            and not facets.joined_tables[cast(str, facets.selected_table)]
        ):
            raise exc.DisconnectedTable(table=facets.selected_table)

        # ensure that all joins were joined on columns that exist on the joined tables
        if facets.bad_joins:
            raise exc.BogusJoinedTable(
                table=facets.bad_joins[0],
            )

        # all columns specified in the join conditions are automatically included in the
        # condition column allowlist
        allowed_join_conditions = set()
        for join_spec in self.allowed_joins():
            if join_spec == ANY_JOIN:
                continue
            allowed_join_conditions.add(join_spec.first)
            allowed_join_conditions.add(join_spec.second)

        # check the condition column allowlist
        for fq_column in facets.condition_columns:
            if fq_column in allowed_join_conditions:
                continue

            if not self.condition_column_allowed(fq_column):
                raise exc.IllegalConditionColumn(
                    column=fq_column,
                )

        # get all of the constraints that the query MUST be constrained by in
        # the WHERE clause
        for constraint in self.required_constraints():
            if constraint not in facets.required_constraints:
                raise exc.MissingRequiredConstraint(
                    column=constraint.fq_column,
                    placeholder=constraint.placeholder,
                )

        # verify that the query is constrained by at least one of the
        # requester's identities. this means that the results of the query will
        # be restricted to data that only the requester has access to.
        #
        # we look at both the identities returned explicitly from the
        # `requester_identities` method, and also the identities that have been
        # annotated in the join conditions.
        req_ids = self.requester_identities()
        join_identities = chain.from_iterable(
            j.requester_identities for j in self.allowed_joins()
        )
        all_req_identities = set(chain(req_ids, join_identities))
        if all_req_identities:
            found_id = False
            for one_id in all_req_identities:
                if one_id in facets.required_constraints:
                    found_id = True
                    break
            if not found_id:
                raise exc.MissingRequiredIdentity(identities=all_req_identities)

        # check that the query limits the rows correctly, if we restrict to a limit
        if (limit := self.max_limit()) is not None:
            if facets.limit > limit:
                raise exc.TooManyRows(limit=facets.limit)

        # check that every function used has been allowlisted
        for fn in facets.functions:
            if not self.can_use_function(fn):
                raise exc.IllegalFunction(function=fn)
