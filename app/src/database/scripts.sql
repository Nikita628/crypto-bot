select * from trade
order by id;

select strategy, avg(profit_percentage) as avg_profit_percentage
from trade
group by strategy;

select * from trade
where strategy = 'dual_momentum'
order by entry_date