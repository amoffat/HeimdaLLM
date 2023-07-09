import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.common import RequiredConstraint
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import CustomerConstraints


def test_required_identity():
    bifrost = Bifrost.mocked(CustomerConstraints())

    query = """select Customer.CustomerId from Customer"""

    with pytest.raises(exc.MissingRequiredIdentity) as excinfo:
        bifrost.traverse(query)

    e = excinfo.value
    assert e.identities == {
        RequiredConstraint(
            column="Customer.CustomerId",
            placeholder="customer_id",
        ),
        RequiredConstraint(
            column="Invoice.CustomerId",
            placeholder="customer_id",
        ),
    }

    query = """
    select Customer.CustomerId from Customer
    where Customer.CustomerId=:customer_id
    """
    bifrost.traverse(query)


def test_where_circumvent_with_precedence():
    """check that we cannot pay lip service to a required condition by
    putting it in an "OR" clause that would never evaluate to true."""

    # this query uses parentheses to ensure precedence
    query = """
SELECT Track.Name
FROM Track
INNER JOIN InvoiceLine ON Track.TrackId = InvoiceLine.TrackId
INNER JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId
INNER JOIN Customer ON Invoice.CustomerId = Customer.CustomerId
WHERE
    (
        Invoice.InvoiceDate >= date('now', '-1 month')
        AND Customer.CustomerId = :customer_id
    )
    OR Customer.CustomerId > 0
LIMIT 20;
"""

    bifrost = Bifrost.mocked(CustomerConstraints())

    with pytest.raises(exc.MissingRequiredIdentity):
        bifrost.traverse(query)


def test_where_no_circumvent_and_very_nested():
    """a query with a very nested where clause, but does not try to circumvent
    the required constraint"""
    query = """
SELECT Track.Name
FROM Track
INNER JOIN InvoiceLine ON Track.TrackId = InvoiceLine.TrackId
INNER JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId
INNER JOIN Customer ON Invoice.CustomerId = Customer.CustomerId
WHERE
    (
        Invoice.InvoiceDate >= date('now', '-1 month')
        AND (
            1=1
            AND (
                Customer.CustomerId = :customer_id
            )
            AND (
                1=2
                OR 2=2
            )
        )
    )
"""

    bifrost = Bifrost.mocked(CustomerConstraints())
    bifrost.traverse(query)


def test_top_level_where_circumvention():
    """checks that we cannot circumvent a required constraint by specifying it
    but making it optional with an OR clause."""

    # no circumvention
    query = """
SELECT Track.Name
FROM Track
INNER JOIN InvoiceLine ON Track.TrackId = InvoiceLine.TrackId
INNER JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId
INNER JOIN Customer ON Invoice.CustomerId = Customer.CustomerId
WHERE
    Invoice.InvoiceDate >= date('now', '-1 month')
    AND Customer.CustomerId = :customer_id
    AND Customer.CustomerId > 0
"""

    bifrost = Bifrost.mocked(CustomerConstraints())
    bifrost.traverse(query)

    # same query, but with the required constraint circumvented with "OR"
    query = """
SELECT Track.Name
FROM Track
INNER JOIN InvoiceLine ON Track.TrackId = InvoiceLine.TrackId
INNER JOIN Invoice ON InvoiceLine.InvoiceId = Invoice.InvoiceId
INNER JOIN Customer ON Invoice.CustomerId = Customer.CustomerId
WHERE
    Invoice.InvoiceDate >= date('now', '-1 month')
    AND (Customer.CustomerId = :customer_id
    OR Customer.CustomerId > 0)
"""
    with pytest.raises(exc.MissingRequiredIdentity):
        bifrost.traverse(query)


def test_where_ambiguity():
    query = """
SELECT track.id
FROM track
WHERE
    (
        3=3
        AND (
            1=:timestamp
            AND (
                Customer.CustomerId = :customer_id
            )
            AND (
                1=2
                OR 2=2
            )
        )
    )
"""

    bifrost = Bifrost.mocked(CustomerConstraints())
    bifrost.traverse(query)
