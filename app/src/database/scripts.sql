select * from trade
order by id;

select strategy, avg(profit_percentage) as avg_profit_percentage
from trade
group by strategy;

select * from trade
where strategy = 'dual_momentum'
order by entry_date



SELECT 
strategy, 

count(*) as total_trades,
sum(profit_percentage) as "total_profit%",

(select count(*) from trade where exit_date is null and strategy = tr.strategy) as opened_trades,
(select sum(profit_percentage) from trade where exit_date is null and strategy = tr.strategy) as "opened_trades_profit%",

(select count(*) from trade where exit_date is not null and strategy = tr.strategy) as closed_trades,
(select sum(profit_percentage) from trade where exit_date is not null and strategy = tr.strategy) as "closed_trades_profit%",

(select count(*) from trade where exit_date is not null and strategy = tr.strategy and profit_percentage > 0) as closed_in_profit_trades,
(select count(*) from trade where exit_date is not null and strategy = tr.strategy and profit_percentage <= 0) as closed_in_loss_trades

from trade tr
group by strategy
order by "total_profit%" desc;