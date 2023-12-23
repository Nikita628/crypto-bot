select strategy, sum(profit_percentage) / count(*) as avg_profit_percentage
from deal
where 
	exit_price is null 
	and exit_date is null
	and strategy = 'dual_momentum'
group by strategy