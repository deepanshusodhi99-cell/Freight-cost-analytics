-- Monthly cost and service trend, with month-over-month change (window function)
WITH monthly AS (
    SELECT
        d.year_month,
        COUNT(*)                         AS shipments,
        ROUND(AVG(f.total_cost), 2)      AS cost_per_shipment,
        ROUND(100.0 * AVG(f.on_time), 1) AS on_time_pct,
        ROUND(AVG(f.origin_dwell_hours), 2) AS avg_dwell_hrs,
        ROUND(AVG(f.diesel_cpl), 1)      AS avg_diesel_cpl
    FROM fact_shipments f
    JOIN dim_date d ON d.date = f.ship_date
    GROUP BY d.year_month
)
SELECT
    year_month, shipments, cost_per_shipment, on_time_pct, avg_dwell_hrs, avg_diesel_cpl,
    ROUND(100.0 * (cost_per_shipment - LAG(cost_per_shipment) OVER (ORDER BY year_month))
          / LAG(cost_per_shipment) OVER (ORDER BY year_month), 1) AS cost_mom_pct
FROM monthly
ORDER BY year_month;
