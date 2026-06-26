-- Query para actualizar budget_data.json
-- Resultado: exportar como JSON array of arrays y reemplazar budget_data.json
SELECT
  kitchen, brand, provider_new_name AS platform, city,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=0 THEN gmv ELSE 0 END)/3.0,0) AS avg0,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=1 THEN gmv ELSE 0 END)/3.0,0) AS avg1,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=2 THEN gmv ELSE 0 END)/3.0,0) AS avg2,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=3 THEN gmv ELSE 0 END)/3.0,0) AS avg3,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=4 THEN gmv ELSE 0 END)/3.0,0) AS avg4,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=5 THEN gmv ELSE 0 END)/3.0,0) AS avg5,
  ROUND(SUM(CASE WHEN EXTRACT(DOW FROM order_day)=6 THEN gmv ELSE 0 END)/3.0,0) AS avg6,
  ROUND(
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=0 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=1 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=2 THEN gmv ELSE 0 END)/3.0*4 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=3 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=4 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=5 THEN gmv ELSE 0 END)/3.0*5 +
    SUM(CASE WHEN EXTRACT(DOW FROM order_day)=6 THEN gmv ELSE 0 END)/3.0*4
  ,0) AS base_julio
FROM fdgy_views.orders_consolidado
WHERE order_state = 'Finalized'
  AND order_day >= CURRENT_DATE - 21
  AND order_day < CURRENT_DATE
  AND gmv > 0
  AND country = 'MEX'
GROUP BY kitchen, brand, provider_new_name, city
ORDER BY base_julio DESC
LIMIT 10000;
