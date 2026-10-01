-- Does origin dwell time drive lateness and detention charges?
WITH bucketed AS (
    SELECT
        CASE
            WHEN origin_dwell_hours <  2 THEN '1) under 2h'
            WHEN origin_dwell_hours <  4 THEN '2) 2-4h'
            WHEN origin_dwell_hours <  6 THEN '3) 4-6h'
            ELSE                              '4) 6h+'
        END AS dwell_bucket,
        on_time, detention_cost, total_cost
    FROM fact_shipments
)
SELECT
    dwell_bucket,
    COUNT(*)                                                      AS shipments,
    ROUND(100.0 * AVG(on_time), 1)                                AS on_time_pct,
    ROUND(AVG(detention_cost), 2)                                 AS avg_detention_cost,
    ROUND(100.0 * AVG(CASE WHEN detention_cost > 0 THEN 1.0 ELSE 0 END), 1) AS pct_with_detention,
    ROUND(SUM(detention_cost), 0)                                 AS total_detention_cost
FROM bucketed
GROUP BY dwell_bucket
ORDER BY dwell_bucket;
