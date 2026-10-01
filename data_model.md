# Data model

Star schema, one fact table and three dimensions.

```
dim_carrier (8 rows)          dim_lane (15 rows)             dim_date (361 rows)
  carrier_id  PK                lane_id  PK                    date  PK
  carrier_name                  origin_dc                      year, month_num, month_name
                                destination                    year_month, quarter, week_of_year
                                distance_km (approx road km)   day_name, is_weekend
                                distance_band                  is_peak_season
        \                            |                          /
         \                           |                         /
          +---------------  fact_shipments (24,000 rows)  ----+
                            shipment_id  PK
                            ship_date  -> dim_date.date
                            carrier_id -> dim_carrier.carrier_id
                            lane_id    -> dim_lane.lane_id
                            pallets, weight_kg
                            planned_transit_days, actual_transit_days
                            on_time (1/0), origin_dwell_hours
                            linehaul_cost, fuel_surcharge, detention_cost, total_cost
                            diesel_cpl (weekly diesel price, cents per litre)
```

Grain of the fact table: one row per shipment.
Distances are approximate road kilometres, rounded. Carrier names are fictional.

## What is baked into the generator

The data is synthetic. These relationships were put in on purpose, so the analysis
has something to find. **The findings therefore show that the method works, not that
the world behaves this way.**

| Mechanism | How it is built in |
|---|---|
| One carrier is cheapest but weak on long lanes | lowest $/km, large on-time penalty on lanes over 800 km |
| One carrier is premium and reliable | highest $/km, smallest long-haul penalty |
| Dwell time hurts service and adds cost | on-time probability drops for origin dwell above 3h; detention billed at $85/h beyond 2h free time on 75% of shipments |
| Peak season (Nov 15 - Dec 24) | 35% more volume, 35% longer dwell, 5-point on-time penalty |
| Fuel surcharge follows diesel price | surcharge % of linehaul = (diesel cpl - 110) x 0.35%, capped at 50% |

Everything else (pallet counts, weights, noise on linehaul cost) is random.
