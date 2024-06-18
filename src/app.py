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


all_columns = ['Symbol', 'Name', 'Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter', 
               'MarketCapitalization', 'PERatio', 'DividendYield', 'ProfitMargin', 'OperatingMargin', 
               'ReturnOnAssets', 'ReturnOnEquity', 'QuarterlyEarningsGrowthYOY', 'AnalystTargetPrice', 
               'AnalystRatingStrongBuy', 'AnalystRatingBuy', 'AnalystRatingHold', 'AnalystRatingSell', 
               'AnalystRatingStrongSell', 'TrailingPE', 'ForwardPE', 'PriceToSalesRatio', 'PriceToBookRatio', 
               'EVToEBITDA', 'Beta', 'Week52High', 'Week52Low', 'Day50MovingAverage', 'Day200MovingAverage']


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)

app.layout = dbc.Container(
    [
        dcc.Store(id='store-data', storage_type='session'),
        dbc.Row(dbc.Col(banner), className="m-3"),
        html.H2("XSelect", style={"text-align": "center", "margin-top": "10px"}),
        dbc.Row(dbc.Col(dbc.Label("Disclaimer: Information contained on this Website is not financial or investment advice and is meant for educational purposes only.", 
                                  style={"textAlign": "left"}, size='sm'), width=9), justify='center'),
        html.H4("Use tabs to navigate", style={"text-align": "center", "margin-top": "10px", "margin-bottom": "10px"}),

        dcc.Tabs([
            dcc.Tab(label='Company Overviews', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select columns to display:"),
                        dcc.Dropdown(
                            id='column-selector',
                            options=[{"label": col, "value": col} for col in all_columns],
                            value=['Symbol', 'Name', 'Sector', 'Industry', 'ProfitMargin'],  
                            multi=True
                        )
                    ], width=12)
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select sector:"),
                        dcc.Dropdown(
                            id='sector-selector',
                            options=[{"label": sector, "value": sector} for sector in overview['Sector'].unique()],
                            value=None,
                            multi=True
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Select industry:"),
                        dcc.Dropdown(
                            id='industry-selector',
                            options=[{"label": industry, "value": industry} for industry in overview['Industry'].unique()],
                            value=None,
                            multi=True
                        )
                    ], width=6)
                ], className="mb-4"),
                dash_table.DataTable(
                    id='table',
                    page_size=10,
                    page_action='native',
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

@app.callback(
    Output('store-data', 'data'),
    Input('column-selector', 'value'),
    Input('sector-selector', 'value'),
    Input('industry-selector', 'value')
)
def store_selections(selected_columns, selected_sectors, selected_industries):
    return {
        'selected_columns': selected_columns,
        'selected_sectors': selected_sectors,
        'selected_industries': selected_industries
    }

@app.callback(
    Output('column-selector', 'value'),
    Output('sector-selector', 'value'),
    Output('industry-selector', 'value'),
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('store-data', 'data'),
    State('column-selector', 'value'),
    State('sector-selector', 'value'),
    State('industry-selector', 'value')
)
def update_table(stored_data, selected_columns, selected_sectors, selected_industries):
    if stored_data:
        selected_columns = stored_data['selected_columns']
        selected_sectors = stored_data['selected_sectors']
        selected_industries = stored_data['selected_industries']
    
    filtered_df = overview.copy()
    
    if selected_sectors:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectors)]
    
    if selected_industries:
        filtered_df = filtered_df[filtered_df['Industry'].isin(selected_industries)]
    
    columns = [{"name": col, "id": col} for col in selected_columns]
    data = filtered_df[selected_columns].to_dict('records')
    return selected_columns, selected_sectors, selected_industries, columns, data

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)