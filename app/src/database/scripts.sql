select * from deal
order by id;

select strategy, avg(profit_percentage) as avg_profit_percentage
from deal
where 
	exit_price is null 
	and exit_date is null
	and strategy = 'dual_momentum'
group by strategy;