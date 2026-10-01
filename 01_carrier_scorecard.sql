-- Carrier scorecard: cost, service, and detention exposure in one view
SELECT
    c.carrier_name,
    COUNT(*)                                                    AS shipments,
    ROUND(SUM(f.total_cost), 0)                                 AS total_cost,
    ROUND(AVG(f.total_cost), 2)                                 AS cost_per_shipment,
    ROUND(SUM(f.total_cost) / SUM(l.distance_km), 3)            AS cost_per_km,
    ROUND(100.0 * AVG(f.on_time), 1)                            AS on_time_pct,
    ROUND(AVG(f.origin_dwell_hours), 2)                         AS avg_dwell_hrs,
    ROUND(100.0 * SUM(f.detention_cost) / SUM(f.total_cost), 1) AS detention_pct_of_cost
FROM fact_shipments f
JOIN dim_carrier c ON c.carrier_id = f.carrier_id
JOIN dim_lane    l ON l.lane_id    = f.lane_id
GROUP BY c.carrier_name
ORDER BY on_time_pct DESC;
