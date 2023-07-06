import pytest

from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost
from heimdallm.bifrosts.sql.utils import JoinCondition

from .utils import CustomerConstraints, PermissiveConstraints


def test_required_constraint_in_join():
    """sometimes LLMs will put a required constraint in a join clause, not a
    where clause. ensure that we allow this to satisfy a required constraint."""
    query = """
    SELECT a.Name AS ArtistName, i.InvoiceDate AS PurchaseDate
FROM Artist a
JOIN Album al ON a.ArtistId = al.ArtistId
JOIN Track t ON al.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
JOIN Invoice i ON il.InvoiceId = i.InvoiceId AND i.CustomerId = :customer_id
WHERE i.InvoiceDate <= :timestamp
LIMIT 20;
"""
    bifrost = Bifrost.mocked(CustomerConstraints())
    bifrost.traverse(query)

    # same query, minus the required join constraint
    query = """
SELECT a.Name AS ArtistName, i.InvoiceDate AS PurchaseDate
FROM Artist a
JOIN Album al ON a.ArtistId = al.ArtistId
JOIN Track t ON al.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
JOIN Invoice i ON il.InvoiceId = i.InvoiceId
WHERE i.InvoiceDate <= :timestamp
LIMIT 20;
"""

    with pytest.raises(exc.MissingRequiredIdentity):
        bifrost.traverse(query)


def test_join_allowlist():
    """ensure that we can discriminate on joins"""

    class JoinAllowlist(PermissiveConstraints):
        def select_column_allowed(self, fq_column):
            return fq_column.name in {"subscriber.name"}

        def allowed_joins(self):
            return [
                JoinCondition("subscriber.provider_id", "provider.id"),
            ]

    bifrost = Bifrost.mocked(JoinAllowlist())

    # allowed join
    query = """
select s.name
from subscriber s
join provider p on s.provider_id = p.id
    """
    bifrost.traverse(query)

    # disallowed join
    query = """
select s.name
from subscriber s
join preferences p on s.subscriber_id = s.id
    """
    with pytest.raises(exc.BogusJoinedTable):
        bifrost.traverse(query)


def test_unconnected_select():
    """a selected table must always be connected to other tables, if other tables are
    joined in the query"""
    query = """
select s.name
from subscriber s
join provider p on other_table.provider_id = p.id
"""

    class JoinAllowlist(PermissiveConstraints):
        def select_column_allowed(self, fq_column):
            return fq_column.name in {"subscriber.name"}

        def allowed_joins(self):
            return [
                JoinCondition("provider.id", "other_table.provider_id"),
            ]

    bifrost = Bifrost.mocked(JoinAllowlist())
    with pytest.raises(exc.DisconnectedTable):
        bifrost.traverse(query)
