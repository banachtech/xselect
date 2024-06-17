import itertools
import pandas as pd
import numpy as np
import json
import hashlib
import statistics
from scipy.optimize import minimize_scalar
from dash import dash, Dash, dcc, html, Input, Output, State, no_update, dash_table
from datetime import datetime

import sys
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
sys.path.append(base_dir)

import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from sqlalchemy import create_engine
from src.default_settings import *
from helpers.layout import *
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)

logo = base64.b64encode(open('../assets/logo.png', 'rb').read()).decode('utf-8')
banner = html.Header(
        html.Img(src=f'data:image/png;base64,{logo}', alt='Banner', height='60px'),
        style={'textAlign': 'center'}
)

# connect to db
eng1 = create_engine(FINANCIALS_DB_URL)

overview = pd.read_sql("SELECT * FROM company_overviews", con=eng1)

prices = pd.read_sql("SELECT * FROM historical_prices", con=eng1, parse_dates=['timestamp']) # format the dataframe so symbols are columns
prices = prices.pivot(index='timestamp', columns='symbol', values='adjusted_close')

quaterly_earnings = pd.read_sql("SELECT * FROM quaterly_earnings", con=eng1)


# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(banner), className="m-3"),
        html.H2("XSelect", style={
            "text-align": "center", "margin-top": "10px"}),
        dbc.Row(dbc.Col(dbc.Label("Disclaimer: Information contained on this Website is not financial or investment advice and is meant for educational purposes only.", style={
            "textAlign": "left"}, size='sm'), width=9), justify='center'),
        html.H4("Use tabs to navigate", style={
            "text-align": "center", "margin-top": "10px", "margin-bottom": "10px"}),
            dcc.Tabs([
                dcc.Tab(label='Company Overviews', children=[
                    dash_table.DataTable(
                        id='table',
                        columns=[
                            {"name": col, "id": col} for col in ['Symbol', 'Name', 'Sector', 'Industry', 'ProfitMargin']
                        ],
                        data=overview.to_dict('records'),
                        page_size=10,  # Set the number of rows per page
                        page_action='native',  # Enable native pagination
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                        style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                        style_cell={'textAlign': 'left'},
                        style_as_list_view=True,
                    )
                ])

            ])
    ]
)


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)