/* 9b83e3cc9096238e3a3666c857c99d2de4f6034e85483a9454edcd3b52a8015e */
SELECT c.category_id, COUNT(r.rental_id) AS num_movies_rented
FROM customer AS cu
JOIN rental AS r ON cu.customer_id = r.customer_id
JOIN inventory AS i ON r.inventory_id = i.inventory_id
JOIN film_category AS fc ON i.film_id = fc.film_id
JOIN category AS c ON fc.category_id = c.category_id
WHERE cu.customer_id = :customer_id
GROUP BY c.category_id
LIMIT 20;
