-- Peak season (Nov 15 - Dec 24) vs the rest of the year
SELECT
    CASE d.is_peak_season WHEN 1 THEN 'Peak season' ELSE 'Rest of year' END AS period,
    COUNT(*)                              AS shipments,
    ROUND(AVG(f.total_cost), 2)           AS cost_per_shipment,
    ROUND(AVG(f.detention_cost), 2)       AS avg_detention_cost,
    ROUND(AVG(f.origin_dwell_hours), 2)   AS avg_dwell_hrs,
    ROUND(100.0 * AVG(f.on_time), 1)      AS on_time_pct
FROM fact_shipments f
JOIN dim_date d ON d.date = f.ship_date
GROUP BY d.is_peak_season
ORDER BY d.is_peak_season DESC;
