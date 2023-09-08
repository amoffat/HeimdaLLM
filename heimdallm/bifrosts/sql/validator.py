from abc import abstractmethod
from itertools import chain
from typing import Optional, Sequence, cast

from lark import Lark, ParseTree, Token
from lark.exceptions import VisitError
from lark.reconstruct import Reconstructor

from heimdallm.bifrost import Bifrost
from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.bifrost import Bifrost as _SQLBifrost
from heimdallm.constraints import ConstraintValidator as _BaseConstraintValidator

from .common import ANY_JOIN, FqColumn, JoinCondition, ParameterizedConstraint
from .visitors.aliases import AliasCollector
from .visitors.facets import FacetCollector, Facets


class ConstraintValidator(_BaseConstraintValidator):
    """
    This validator checks different of a SQL query. You are intended to derive this
    class and implement its methods."""

    @abstractmethod
    def requester_identities(self) -> Sequence[ParameterizedConstraint]:
        """Returns the possible identities of the requester, as represented in the
        database. This is used to instruct the LLM how to constrain the query that it
        generates. Only one of these identities needs to match for the query to be
        compliant.

        The reason that we return a sequence, and not a single identity, is that
        sometimes an LLM will specify the constraint as part of a ``JOIN`` condition,
        and not a ``WHERE`` condition. In that case, the column in the JOIN condition
        may not match the column you expect.

        For example, consider selecting films for a customer, constrained by the
        customer id. The LLM may give you a query like this:

        .. code-block:: sql

            SELECT f.title
            FROM film f
            JOIN inventory i ON f.film_id=i.film_id
            JOIN rental r ON i.inventory_id=r.inventory_id
            JOIN customer c ON r.customer_id=c.customer_id
            WHERE c.customer_id=:customer_id

        Or you may receive a query like this:

        .. code-block:: sql

            SELECT f.title
            FROM film f
            JOIN inventory i ON f.film_id=i.film_id
            JOIN rental r
                ON i.inventory_id=r.inventory_id
                AND r.customer_id=:customer_id

        Both ``rental.customer_id`` and ``customer.customer_id`` are valid requester
        identities, so ou need to specify both of them by returning a
        :class:`heimdallm.bifrosts.sql.common.RequiredConstraint` for each of them.

        :return: The sequence of possible requester identities.
        """
        raise NotImplementedError(
            "You must explicitly provide the requester identity, "
            "or an empty list for full access (dangerous)"
        )

    @abstractmethod
    def parameterized_constraints(self) -> Sequence[ParameterizedConstraint]:
        """
        Returns a sequence of constraints that must exist in either the ``WHERE`` clause
        of the query or in a ``JOIN`` condition. It doesn't matter where the constraint
        is, as long as it exists and is required (i.e. not part of an optional
        condition).

        :return: The sequence of required constraints.
        """
        raise NotImplementedError(
            "You must explicitly provide a sequence of parameterized constraints, "
            "or an empty list for no constraints"
        )

    @abstractmethod
    def select_column_allowed(self, column: FqColumn) -> bool:
        """Check that a fully-qualified column is allowed to be selected in the
        ``SELECT`` clause. Use this to restrict the columns and tables that can be
        selected.

        This value is also used to inform :doc:`/reconstruction`. Columns that do not
        pass this check will be removed from the query.

        :param column: The fully-qualified column.
        :return: Whether or not the column is allowed to be selected.
        """
        return False

    @abstractmethod
    def allowed_joins(self) -> Sequence[JoinCondition]:
        """Returns all of the tables allowed to be connected to the query via a
        ``JOIN`` and the equi-join conditions that must be met for the join to be valid.

        :return: The sequence of allowed joins.
        """
        return []

    @abstractmethod
    def max_limit(self) -> Optional[int]:
        """Return the maximum number of rows that can be returned by a query. if
        None, there is no limit.

        This value is also used to inform :doc:`/reconstruction`. If this function
        provides a limit, but the query does not, or the query provides a higher limit,
        the query will be reconstructed to include the correct limit.

        :return: The maximum number of rows that can be returned by a query, or None if
            unlimited.
        """
        return None

    @abstractmethod
    def can_use_function(self, function: str) -> bool:
        """
        Returns whether or not a SQL function is allowed to be used anywhere in the
        query. By default, this checks the function against the list of safe functions
        that we have curated by hand.

        :param function: The *lowercase* name of the function.
        :return: Whether or not the function is allowed.
        """
        raise NotImplementedError

    def condition_column_allowed(self, fq_column: FqColumn) -> bool:
        """
        Checks if a column is allowed to be used in a ``WHERE``, ``JOIN``, ``HAVING``,
        or ``ORDER BY``. By default, this calls :meth:`select_column_allowed`, but if
        you override this method and want to preserve that behavior, you should call
        yourself.

        :param fq_column: The fully-qualified column.
        :return: Whether or not the column is allowed to be used in a condition.
        """
        # let's default to "if you can see it, you can use it"
        return self.select_column_allowed(fq_column)

    def fix(self, bifrost: Bifrost, grammar: Lark, tree: ParseTree) -> str:
        """A parse tree may be valid SQL, but it may not be valid according to
        the validator's constraints. we may be able to make intelligent
        decisions about those constraints, and fix the parse tree though, for
        example, by adding a limit to a query.

        :meta private:
        """

        # gets around a circular import issue
        from heimdallm.bifrosts.sql import reconstruct

        transform = reconstruct.ReconstructTransformer(
            self,
            cast(_SQLBifrost, bifrost).reserved_keywords(),
        )
        try:
            fixed_tree = transform.transform(tree)
        except VisitError as e:
            if isinstance(e.orig_exc, exc.BaseException):
                raise e.orig_exc
            raise e

        def special(sym):
            return Token("IGNORE", sym.name)

        output = Reconstructor(grammar, {"_WS": special}).reconstruct(
            fixed_tree,
            postproc=reconstruct.postproc,
        )
        return output

    def validate(self, bifrost: Bifrost, untrusted_input: str, tree: ParseTree):
        """Analyze the parsed tree and validate it against our SQL constraints

        :param untrusted_input: The original query string. This is passed in so that if
            we need to raise an exception that references it, we can.
        :param tree: The parsed tree from the original query string.

        :meta private:
        """
        try:
            alias_collector = AliasCollector(
                cast(_SQLBifrost, bifrost).reserved_keywords()
            )
            alias_collector.visit(tree)

            facets = Facets()
            facet_collector = FacetCollector(
                facets,
                alias_collector,
                cast(_SQLBifrost, bifrost).reserved_keywords(),
            )
            facet_collector.visit(tree)
        except exc.GeneralParseError:
            raise exc.InvalidQuery(query=untrusted_input)

        # check the select column allowlist
        for fq_column in facets.selected_columns:
            if not self.select_column_allowed(fq_column):
                raise exc.IllegalSelectedColumn(column=fq_column.name)

        for scope in facets.scopes.values():
            # check the join condition allowlist
            any_join_cond_allowed = ANY_JOIN in self.allowed_joins()
            for table, join_specs in scope.joined_tables.items():
                for join_spec in join_specs:
                    allowed = any_join_cond_allowed or join_spec in self.allowed_joins()
                    if not allowed:
                        raise exc.IllegalJoinTable(join=join_spec)

            # ensure that the selected table is joined to another table, if joins exist
            if (
                scope.joined_tables
                and not scope.joined_tables[cast(str, scope.selected_table)]
            ):
                raise exc.DisconnectedTable(table=cast(str, scope.selected_table))

            # ensure that all joins were joined on columns that exist on the joined
            # tables
            if scope.bad_joins:
                raise exc.BogusJoinedTable(
                    table=scope.bad_joins[0],
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
        for constraint in self.parameterized_constraints():
            if constraint not in facets.parameterized_constraints:
                raise exc.MissingParameterizedConstraint(
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
                if one_id in facets.parameterized_constraints:
                    found_id = True
                    break
            if not found_id:
                raise exc.MissingRequiredIdentity(identities=all_req_identities)

        # check that the query limits the rows correctly, if we restrict to a limit
        if (max_limit := self.max_limit()) is not None:
            for limit in facets.limits.values():
                if limit is None or limit > max_limit:
                    raise exc.TooManyRows(limit=limit)

        # check that every function used has been allowlisted
        for fn in facets.functions:
            if not self.can_use_function(fn):
                raise exc.IllegalFunction(function=fn)
