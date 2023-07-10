/* 60d40d9c8b3a6f45979899a12cf98fd4ef0dbc4c757e6a9e230d442593c30939 */
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