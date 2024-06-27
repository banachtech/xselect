import itertools
import pandas as pd
import numpy as np
import json
import hashlib
import statistics
from scipy.optimize import minimize_scalar
from dash import dash, Dash, dcc, html, Input, Output, State, no_update, dash_table
from datetime import datetime
from data import check_symbol

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
from data import main
logging.basicConfig(filename='app.log', level=logging.INFO)

logo = base64.b64encode(open('../assets/logo.png', 'rb').read()).decode('utf-8')
banner = html.Header(
        html.Img(src=f'data:image/png;base64,{logo}', alt='Banner', height='60px'),
        style={'textAlign': 'center'}
)

# connect to db
eng1 = create_engine(FAKE_FINANCIALS_DB_URL)
eng2 = create_engine(FINANCIALS_DB_URL)

overview = pd.read_sql("SELECT * FROM company_overviews", con=eng1)

prices = pd.read_sql("SELECT * FROM historical_prices", con=eng2, parse_dates=['timestamp']) # CHANGE TO ENG1 for PRODUCTION!!!!!!
prices = prices.pivot(index='timestamp', columns='symbol', values='adjusted_close')

quaterly_earnings = pd.read_sql("SELECT * FROM quaterly_earnings", con=eng2)


all_columns = ['Symbol', 'Name', 'Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter', 
               'MarketCapitalization', 'PERatio', 'DividendYield', 'ProfitMargin', 'OperatingMargin', 
               'ReturnOnAssets', 'ReturnOnEquity', 'QuarterlyEarningsGrowthYOY', 'AnalystTargetPrice', 
               'AnalystRatingStrongBuy', 'AnalystRatingBuy', 'AnalystRatingHold', 'AnalystRatingSell', 
               'AnalystRatingStrongSell', 'TrailingPE', 'ForwardPE', 'PriceToSalesRatio', 'PriceToBookRatio', 
               'EVToEBITDA', 'Beta', 'Week52High', 'Week52Low', 'Day50MovingAverage', 'Day200MovingAverage']

# splitting columns for the visualization part
some_columns = ['Name', 'Symbol','Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter']
remaining_columns = [col for col in all_columns if col not in some_columns]

# removing duplicates for overview section
unique_companies = overview.drop_duplicates(subset=['Name', 'Symbol','Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter'])


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
                            options=[{"label": col, "value": col} for col in some_columns],
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
                dash_table.DataTable( # table for the overview
                    id='table',
                    columns=[{"name": col, "id": col} for col in some_columns],
                    data=unique_companies.to_dict('records'),
                    page_size=10,
                    page_action='native',
                    style_table={'overflowX': 'auto'},
                    style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                    style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                    style_cell={'textAlign': 'left'},
                    style_as_list_view=True,
                ),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select metric to graph:"), 
                        dcc.Dropdown(
                            id='metric-selector',
                            options=[{"label": col, "value": col} for col in remaining_columns if col != 'Symbol'],
                            value='ProfitMargin',
                            clearable=False,
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Select companies to graph:"),
                        dcc.Dropdown(
                            id='company-selector',
                            options=[{"label": row['Name'], "value": row['Symbol']} for index, row in unique_companies.iterrows()],
                            value=[],
                            multi=True,
                            clearable=False
                        )
                    ], width=6)
                ], className="mb-4"),
                dcc.Graph(id='timeseries-graph') # timeseries graph
            ]),
            dcc.Tab(label='Settings', children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Select frequency:", className="me-2"),
                        dcc.Dropdown(
                            id='frequency-selector',
                            options=[
                                {"label": "Daily", "value": "daily"},
                                {"label": "Weekly", "value": "weekly"},
                                {"label": "Monthly", "value": "monthly"}
                            ],
                            value='daily',
                            style={'width': '100%'}
                        ),
                    ], width=6, style={'padding': '10px'}),
                ], justify='center', className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Enter ticker:", className="me-2"),
                        dcc.Input(
                            id='ticker-input',
                            type='text',
                            value='',
                            placeholder='Enter ticker symbol',
                            style={'width': '80%'}
                        ),
                        dbc.Button("Check Ticker", id='check-ticker-btn', color='primary', className='ms-2'),
                    ], width=6, style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'padding': '10px'}),
                ], justify='center', className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div(id='ticker-result')
                    ], width=12, style={'padding': '10px'}),
                ], justify='center', className="mb-4")
            ])
        ]),
        dcc.Interval(
            id='interval-component',
            interval=1209600000,  # 1,209,600,000 ms = 2 weeks
            n_intervals=0
        ),
    ]
)

# @app.callback(
#     Output('timeseries-graph', 'figure'),
#     Input('metric-selector', 'value'),
#     Input('company-selector', 'value')
# )
# def update_timeseries_graph(metric, companies):
#     fig = go.Figure()

#     if companies:
#         for symbol in companies:
#             df = pd.read_sql(f"SELECT timestamp, {metric} FROM historical_prices WHERE symbol='{symbol}'", con=eng1)
#             fig.add_trace(go.Scatter(x=df['timestamp'], y=df[metric], mode='lines+markers', name=symbol))

#     fig.update_layout(
#         title=f'{metric} Over Time',
#         xaxis_title='Date',
#         yaxis_title=metric,
#         hovermode='x',
#         template='plotly_dark'
#     )

#     return fig

# graphing the timeseries graph for overivew data
@app.callback(
    Output('timeseries-graph', 'figure'),
    Input('metric-selector', 'value'),
    Input('company-selector', 'value')
)
def update_timeseries_graph(metric, companies):
    fig = go.Figure()

    if companies:
        for symbol in companies:
            query = f"""
            SELECT DateAppend, {metric}
            FROM company_overviews
            WHERE symbol = '{symbol}'
            ORDER BY current_date
            """
            df = pd.read_sql(query, con=eng1)
            print(df) 
            if not df.empty:
                fig.add_trace(go.Scatter(x=df['DateAppend'], y=df[metric], mode='lines+markers', name=symbol))

    fig.update_layout(
        title=f'{metric} Over Time',
        xaxis_title='Date',
        yaxis_title=metric,
        hovermode='x',
        template='simple_white'
    )

    return fig

# storing the selected columns, sectors, and industries
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

# updating the table
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
    
    filtered_df = unique_companies.copy()
    
    if selected_sectors:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectors)]
    
    if selected_industries:
        filtered_df = filtered_df[filtered_df['Industry'].isin(selected_industries)]
    
    columns = [{"name": col, "id": col} for col in selected_columns]
    data = filtered_df[selected_columns].to_dict('records')
    return selected_columns, selected_sectors, selected_industries, columns, data


# callback to check ticker and update the result
@app.callback(
    Output('ticker-result', 'children'),
    Input('check-ticker-btn', 'n_clicks'),
    State('ticker-input', 'value')
)
def check_ticker(n_clicks, ticker):
    if n_clicks:
        result = check_symbol(ticker)
        if isinstance(result, pd.DataFrame):
            return dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Ticker Data")),
                    dbc.ModalBody(
                        dash_table.DataTable(
                            data=result.to_dict('records'),
                            columns=[{'name': col, 'id': col} for col in result.columns],
                            style_table={'overflowX': 'auto'},
                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                            style_cell={'textAlign': 'left'},
                            style_as_list_view=True,
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close-modal", className="ml-auto")
                    ),
                ],
                id="modal",
                is_open=True,
            )
        else:
            return html.Div("Ticker does not exist", style={'color': 'red'})
    return ""

# floating table that shows if a ticker exists
@app.callback(
    Output("modal", "is_open"),
    Input("close-modal", "n_clicks"),
    [State("modal", "is_open")],
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# interval component to update the database
@app.callback(
    Output('store-data', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_data(n):
    main()  
    return {}  

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)