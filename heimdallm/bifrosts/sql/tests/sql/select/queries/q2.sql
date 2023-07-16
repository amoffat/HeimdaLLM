/* e31f53a97bec765758232f35ecc8ea67e3d6c340ad8e7693d8392d1406382554 */
SELECT f.title, f.rating, f.release_year
FROM film f
INNER JOIN inventory i ON f.film_id = i.film_id
INNER JOIN rental r ON i.inventory_id = r.inventory_id
INNER JOIN customer c ON r.customer_id = c.customer_id
WHERE c.customer_id = :customer_id
AND (f.rating = 'R' OR f.rating = 'NC-17')
AND f.release_year IS NOT NULL
ORDER BY f.release_year DESC
LIMIT 20;