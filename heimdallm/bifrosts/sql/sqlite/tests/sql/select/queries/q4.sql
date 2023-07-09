/* 55c49b2882328417fba2d4625e6ca6c9e5ccff2fd313c032bc163648cf195ab8 */
SELECT f.title, r.rental_date, r.return_date, 
       (julianday(r.return_date) - julianday(r.rental_date)) AS days_rented
FROM rental r
JOIN inventory i ON r.inventory_id = i.inventory_id
JOIN customer c ON r.customer_id = c.customer_id
JOIN film f ON i.film_id = f.film_id
WHERE c.customer_id = :customer_id
ORDER BY days_rented DESC
LIMIT 5;