import pandas as pd
from classes import PivotMaker
from funcs import show_graph_objects


pm = PivotMaker(36)
df_pivots: pd.DataFrame = pm.prepare_dataframe('year_month', 'sift_out', 'make_pivots')

df_last_month: pd.DataFrame = pm.get_last_month(df_pivots)
propabilities: dict = pm.get_crossing_probability(df_pivots, 2000)

# Nutzung des Frameworks plotly für den Candle-Stick Chart
show_graph_objects(df_last_month, pm.title, propabilities)

# 1. Die renew Methode zusammen mit get_propabilities machen Probleme und alle selfs greifen auf das gleiche Objekt zu (Call by Object)
