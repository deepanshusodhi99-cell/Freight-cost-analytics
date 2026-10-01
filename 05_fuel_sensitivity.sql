-- How much does the diesel price move the fuel surcharge? (quartiles of diesel price)
WITH q AS (
    SELECT diesel_cpl, fuel_surcharge, linehaul_cost,
           NTILE(4) OVER (ORDER BY diesel_cpl) AS diesel_quartile
    FROM fact_shipments
)
SELECT
    diesel_quartile,
    ROUND(MIN(diesel_cpl), 1)                         AS min_diesel_cpl,
    ROUND(MAX(diesel_cpl), 1)                         AS max_diesel_cpl,
    ROUND(AVG(fuel_surcharge), 2)                     AS avg_fuel_surcharge,
    ROUND(100.0 * SUM(fuel_surcharge) / SUM(linehaul_cost), 1) AS fuel_pct_of_linehaul
FROM q
GROUP BY diesel_quartile
ORDER BY diesel_quartile;
