select * from trade
order by id;

select strategy, avg(profit_percentage) as avg_profit_percentage
from trade
group by strategy;

select * from trade
where strategy = 'dual_momentum'
order by entry_date


------------------ trades statistics ------------------------------
SELECT 
 -- 0.1 fraction of total usdt asset amount used for a trade
    strategy, 
    COUNT(*) AS total_trades,

    ROUND(SUM(profit_percentage * 0.1)::DECIMAL, 3) AS "total_profit%",

    COUNT(*) FILTER (WHERE exit_date IS NULL) AS opened_trades,

    ROUND((SUM(profit_percentage * 0.1) FILTER (WHERE exit_date IS NULL))::DECIMAL, 3) AS "opened_trades_profit%",

    COUNT(*) FILTER (WHERE exit_date IS NOT NULL) AS closed_trades,

    ROUND((SUM(profit_percentage * 0.1) FILTER (WHERE exit_date IS NOT NULL))::DECIMAL, 3) AS "closed_trades_profit%",

    COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND profit_percentage > 0) AS closed_in_profit_trades,

    COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND profit_percentage <= 0) AS closed_in_loss_trades,
	
    ROUND(CAST(COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND profit_percentage > 0) AS DECIMAL) / 
          NULLIF(COUNT(*) FILTER (WHERE exit_date IS NOT NULL), 0) * 100, 2) AS "closed_in_profit_trades%",

    ROUND(CAST(COUNT(*) FILTER (WHERE exit_date IS NOT NULL AND profit_percentage <= 0) AS DECIMAL) / 
          NULLIF(COUNT(*) FILTER (WHERE exit_date IS NOT NULL), 0) * 100, 2) AS "closed_in_loss_trades%"
FROM 
    trade tr
GROUP BY 
    strategy
ORDER BY 
    "total_profit%" DESC;

----------- strategy start date ------------------------------
select strategy, min(entry_date) approximate_strategy_start_date
from trade
group by strategy
order by approximate_strategy_start_date