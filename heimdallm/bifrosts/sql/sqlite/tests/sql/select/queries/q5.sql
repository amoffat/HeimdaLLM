/* a833416117b67090f431965708e9aa891d8386eb42dd84f0612b29ecde0cb94e */
SELECT actor.first_name, actor.last_name, COUNT(film_actor.film_id) AS film_count 
FROM actor 
JOIN film_actor ON actor.actor_id = film_actor.actor_id 
GROUP BY actor.actor_id 
ORDER BY film_count DESC;