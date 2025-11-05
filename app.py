from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
from classes import KMeansClusterMain, BaseLoader
from settings import mariadb_config

def get_stocks():

    stocks = [v[0] for v in loader.select("select * from AllStocksView;")]
    yield stocks

loader = BaseLoader(mariadb_config)
app = Dash()
app.layout = html.Div([
    dcc.Dropdown(['NYC', 'MTL', 'SF'], 'NYC', id='demo-dropdown'),
    html.Div(id='dd-output-container')
])


if __name__ == "__main__":
    app.run(debug=True)
