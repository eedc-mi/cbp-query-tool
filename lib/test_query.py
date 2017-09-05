import pandas as pd
import sqlalchemy as sql
from query import Query

engine = sql.create_engine('sqlite:///V:\Economic Intelligence\Data & Forecasts for MI\CBP Query Tool\June 2016\code\cbp_query_tool\data\data.db')
query = Query(engine)

query.set_target_geo_level('CMA_CA')
query.set_parent_geo_level('Province')
query.set_naics_level(2)
query.set_parent_geo('Quebec')

print query.build_query()
query.get_df()

print query.df.head()

#result = engine.execute('EXPLAIN QUERY PLAN SELECT geo.cma_ca_name, CAST(SUBSTR(CAST(counts.naics_id AS TEXT), 1, 6) AS INT) AS naics_id6, description, SUM([without_employees]) AS [without_employees], SUM([total_with_employees]) AS [total_with_employees], SUM([1_4]) AS [1_4], SUM([5_9]) AS [5_9], SUM([10_19]) AS [10_19], SUM([20_49]) AS [20_49], SUM([50_99]) AS [50_99], SUM([100_199]) AS [100_199], SUM([200_499]) AS [200_499], SUM([500_+]) AS [500_+] FROM counts, geo, naics WHERE counts.da = geo.da AND naics_id6 = naics.naics_id AND prname = "Alberta" GROUP BY naics_id6, geo.cmaname')

##for row in result:
##    print row
