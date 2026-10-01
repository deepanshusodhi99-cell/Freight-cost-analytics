-- On-time % by carrier and distance band (conditional aggregation = pivot)
SELECT
    c.carrier_name,
    ROUND(100.0 * AVG(CASE WHEN l.distance_band = '<300 km'    THEN f.on_time END), 1) AS otp_under_300km,
    ROUND(100.0 * AVG(CASE WHEN l.distance_band = '300-800 km' THEN f.on_time END), 1) AS otp_300_800km,
    ROUND(100.0 * AVG(CASE WHEN l.distance_band = '>800 km'    THEN f.on_time END), 1) AS otp_over_800km
FROM fact_shipments f
JOIN dim_carrier c ON c.carrier_id = f.carrier_id
JOIN dim_lane    l ON l.lane_id    = f.lane_id
GROUP BY c.carrier_name
ORDER BY otp_over_800km DESC;
