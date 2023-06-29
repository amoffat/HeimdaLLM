from typing import Optional, Sequence

from heimdallm.bifrosts.sql.sqlite.select.validator import SQLConstraintValidator
from heimdallm.bifrosts.sql.utils import FqColumn, JoinCondition, RequiredConstraint


class CustomerDataConstraints(SQLConstraintValidator):
    """A relatively-permissive customer constraints validator for the Sakila database.
    This validator allows the customer to access tables joined by their customer id."""

    def requester_identities(self) -> Sequence[RequiredConstraint]:
        """tells our validator that the query must have some constraint, either
        in the WHERE or on a JOIN, that constrains a particular column to a
        named placeholder, whose placeholder value we will pass in at query
        execution time."""
        return [
            RequiredConstraint(
                column="customer.customer_id",
                placeholder="customer_id",
            ),
        ]

    def required_constraints(self) -> Sequence[RequiredConstraint]:
        """additional constraints that must be present in the query, separate
        from the requester's identity. ALL of these constraints must be present
        in the query."""

        # for this demo, we won't require any additional constraints, to give the most
        # freedom.
        return []

    def select_column_allowed(self, fq_column: FqColumn) -> bool:
        """returns True if the query is allowed to select a particular column,
        otherwise False"""

        # for this demo, we'll allow all columns to be selected except "_id" columns. in
        # practice, you'll want to carefully limit this to only the columns that the
        # requester is allowed to see.
        return not fq_column.name.endswith("_id")

    def allowed_joins(self) -> Sequence[JoinCondition]:
        """returns all allowed equi-joins that the query is allowed to make"""
        return (
            # these join conditions have the `identity` kwarg set, meaning that
            # our requester identity can be satisfied if the equi-join condition
            # constraints on the `:customer_id` placeholder. an LLM may do this instead
            # of satisfying the requester identity in the WHERE clause.
            JoinCondition(
                "customer.customer_id",
                "rental.customer_id",
                identity="customer_id",
            ),
            JoinCondition(
                "customer.customer_id",
                "payment.customer_id",
                identity="customer_id",
            ),
            JoinCondition("address.city_id", "city.city_id"),
            JoinCondition("city.country_id", "country.country_id"),
            JoinCondition("customer.address_id", "address.address_id"),
            JoinCondition("customer.store_id", "store.store_id"),
            JoinCondition("film_actor.actor_id", "actor.actor_id"),
            JoinCondition("film_category.category_id", "category.category_id"),
            JoinCondition("film_category.film_id", "inventory.film_id"),
            JoinCondition("film.film_id", "film_actor.film_id"),
            JoinCondition("film.film_id", "film_category.film_id"),
            JoinCondition("film.original_language_id", "language.language_id"),
            JoinCondition("inventory.film_id", "film.film_id"),
            JoinCondition("inventory.inventory_id", "rental.inventory_id"),
            JoinCondition("rental.rental_id", "payment.rental_id"),
            JoinCondition("store.address_id", "address.address_id"),
        )

    def max_limit(self) -> Optional[int]:
        """the maximum number of rows allowed to be returned by the query."""
        return 20

    def condition_column_allowed(self, fq_column: FqColumn) -> bool:
        """return True if the query is allowed to use a particular column in a JOIN or
        WHERE condition"""
        return True


class CustomerGeneralConstraints(SQLConstraintValidator):
    """A constraints validator for general customer access to data that may not be
    theirs, but is not sensitive."""

    def requester_identities(self) -> Sequence[RequiredConstraint]:
        """tells our validator that the query must have some constraint, either
        in the WHERE or on a JOIN, that constrains a particular column to a
        named placeholder, whose placeholder value we will pass in at query
        execution time."""
        return []

    def required_constraints(self) -> Sequence[RequiredConstraint]:
        """additional constraints that must be present in the query, separate
        from the requester's identity. ALL of these constraints must be present
        in the query."""

        # for this demo, we won't require any additional constraints, to give the most
        # freedom.
        return []

    def select_column_allowed(self, fq_column: FqColumn) -> bool:
        """returns True if the query is allowed to select a particular column,
        otherwise False"""

        # for this demo, we'll allow all columns to be selected except "_id" columns. in
        # practice, you'll want to carefully limit this to only the columns that the
        # requester is allowed to see.
        return not fq_column.name.endswith("_id")

    def allowed_joins(self) -> Sequence[JoinCondition]:
        """returns all allowed equi-joins that the query is allowed to make"""
        return (
            JoinCondition("address.city_id", "city.city_id"),
            JoinCondition("city.country_id", "country.country_id"),
            JoinCondition("film_actor.actor_id", "actor.actor_id"),
            JoinCondition("film_category.category_id", "category.category_id"),
            JoinCondition("film_category.film_id", "inventory.film_id"),
            JoinCondition("film.film_id", "film_actor.film_id"),
            JoinCondition("film.film_id", "film_category.film_id"),
            JoinCondition("film.original_language_id", "language.language_id"),
            JoinCondition("inventory.film_id", "film.film_id"),
            JoinCondition("store.address_id", "address.address_id"),
        )

    def max_limit(self) -> Optional[int]:
        """the maximum number of rows allowed to be returned by the query."""
        return 20

    def condition_column_allowed(self, fq_column: FqColumn) -> bool:
        """return True if the query is allowed to use a particular column in a JOIN or
        WHERE condition"""
        return True
