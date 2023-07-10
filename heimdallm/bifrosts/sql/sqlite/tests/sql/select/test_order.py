from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost

from .utils import PermissiveConstraints


def test_order_by_count():
    query = """
SELECT c.customer_id, fc.category_id, category.name
FROM customer c
JOIN rental r ON c.customer_id = r.customer_id
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN film_category fc ON i.film_id = fc.film_id
JOIN category ON fc.category_id = category.category_id
WHERE c.customer_id = :customer_id
GROUP BY c.customer_id, fc.category_id, category.name
ORDER BY COUNT(*) DESC
LIMIT 20;
"""

    bifrost = Bifrost.mocked(PermissiveConstraints())
    bifrost.traverse(query)
