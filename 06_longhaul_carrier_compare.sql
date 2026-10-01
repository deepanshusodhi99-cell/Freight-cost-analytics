-- Long-haul lanes (>800 km) only: who is cheap, who is reliable?
SELECT
    c.carrier_name,
    COUNT(*)                                         AS shipments,
    ROUND(SUM(f.total_cost) / SUM(l.distance_km), 3) AS cost_per_km,
    ROUND(100.0 * AVG(f.on_time), 1)                 AS on_time_pct
FROM fact_shipments f
JOIN dim_carrier c ON c.carrier_id = f.carrier_id
JOIN dim_lane    l ON l.lane_id    = f.lane_id
WHERE l.distance_band = '>800 km'
GROUP BY c.carrier_name
ORDER BY on_time_pct DESC;
