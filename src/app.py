
import pandas as pd
import numpy as np

from scipy.optimize import minimize_scalar
from dash import dash, Dash, dcc, html, Input, Output, State, no_update, dash_table, callback_context
from datetime import datetime
from dash.exceptions import PreventUpdate
from data import check_symbol
import time
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
from data import get_overview,get_prices,get_quaterly_earnings, save_company_overview, save_historical_prices, save_quaterly_earnings
logging.basicConfig(filename='app.log', level=logging.INFO)

logo = base64.b64encode(open('../assets/logo.png', 'rb').read()).decode('utf-8')
banner = html.Header(
        html.Img(src=f'data:image/png;base64,{logo}', alt='Banner', height='60px'),
        style={'textAlign': 'center'}
)

# connect to db
eng1 = create_engine(FAKE_FINANCIALS_DB_URL)
eng2 = create_engine(FINANCIALS_DB_URL)

overview = pd.read_sql("SELECT * FROM company_overviews", con=eng2)
print(overview)

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
                        dbc.Button("Update Ticker", id='update-ticker-btn', color='secondary', className='ms-2'),
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

# Update selectors and store data when user interacts with selectors
@app.callback(
    Output('store-data', 'data'),
    Output('column-selector', 'value'),
    Output('sector-selector', 'value'),
    Output('industry-selector', 'value'),
    Input('column-selector', 'value'),
    Input('sector-selector', 'value'),
    Input('industry-selector', 'value'),
    State('store-data', 'data')
)
def update_selections_and_store(columns, sectors, industries, stored_data):
    if not callback_context.triggered_id:
        raise PreventUpdate
    
    if stored_data is None:
        stored_data = {}
    
    if callback_context.triggered_id == 'column-selector':
        stored_data['selected_columns'] = columns
    elif callback_context.triggered_id == 'sector-selector':
        stored_data['selected_sectors'] = sectors
    elif callback_context.triggered_id == 'industry-selector':
        stored_data['selected_industries'] = industries
    
    return stored_data, stored_data.get('selected_columns', columns), stored_data.get('selected_sectors', sectors), stored_data.get('selected_industries', industries)

# Updating the table
@app.callback(
    Output('table', 'columns'),
    Output('table', 'data'),
    Input('store-data', 'data')
)
def update_table(stored_data):
    if not stored_data:
        raise PreventUpdate

    selected_columns = stored_data.get('selected_columns', [])
    selected_sectors = stored_data.get('selected_sectors', [])
    selected_industries = stored_data.get('selected_industries', [])

    filtered_df = unique_companies.copy()

    if selected_sectors:
        filtered_df = filtered_df[filtered_df['Sector'].isin(selected_sectors)]

    if selected_industries:
        filtered_df = filtered_df[filtered_df['Industry'].isin(selected_industries)]

    columns = [{"name": col, "id": col} for col in selected_columns]
    data = filtered_df[selected_columns].to_dict('records')
    return columns, data


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
    Output('store-data', 'data', allow_duplicate=True),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True
)
def update_data(n):
    query = f"""
            SELECT symbol
            FROM company_overviews
            """
    df = pd.read_sql(query, con=eng1)
    symbols = df["symbol"].tolist()
    print('downloading company overviews ...')
    st = time.time()
    res = []
    for symbol in symbols:
        try:
            print(symbol)
            tmp = get_overview(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            res.append(tmp)

    ed = time.time() - st

    if res:
        res = pd.concat(res, axis=0)
        print(f'{res.shape[0]} symbols processed in {ed:0.2f} seconds')
        save_company_overview(res, eng1)

    # historical stock prices
    print('downloading historical stock prices ...')

    st = time.time()
    ps = []
    for symbol in symbols:
        try:
            tmp = get_prices(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            ps.append(tmp)
    ed = time.time() - st

    if ps:
        ps = pd.concat(ps, axis=1)
        print(f'{ps.shape[1]} symbols processed in {ed:0.2f} seconds')
        save_historical_prices(ps, eng2)

    # quaterly earnings
    print('downloading quaterly earnings ...')
    st = time.time()
    res = []
    for symbol in symbols:
        try:
            tmp = get_quaterly_earnings(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            res.append(tmp)
    ed = time.time() - st

    if res:
        res = pd.concat(res, axis=0)
        print(f'{res.shape[1]} symbols processed in {ed:0.2f} seconds')
        save_quaterly_earnings(res, eng2)
    return {}

# callback to update the ticker based on the input symbol
def update_data_for_symbol(ticker):
    symbols = [ticker]

    # company overviews
    print('downloading company overviews ...')
    st = time.time()
    res = []
    for symbol in symbols:
        try:
            print(symbol)
            tmp = get_overview(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            res.append(tmp)

    ed = time.time() - st

    if res:
        res = pd.concat(res, axis=0)
        print(f'{res.shape[0]} symbols processed in {ed:0.2f} seconds')
        save_company_overview(res, eng1)

    # historical stock prices
    print('downloading historical stock prices ...')

    st = time.time()
    ps = []
    for symbol in symbols:
        try:
            tmp = get_prices(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            ps.append(tmp)
    ed = time.time() - st

    if ps:
        ps = pd.concat(ps, axis=1)
        print(f'{ps.shape[1]} symbols processed in {ed:0.2f} seconds')
        save_historical_prices(ps, eng1)

    # quaterly earnings
    print('downloading quaterly earnings ...')
    st = time.time()
    res = []
    for symbol in symbols:
        try:
            tmp = get_quaterly_earnings(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
            print(e)
        else:
            res.append(tmp)
    ed = time.time() - st

    if res:
        res = pd.concat(res, axis=0)
        print(f'{res.shape[1]} symbols processed in {ed:0.2f} seconds')
        save_quaterly_earnings(res, eng1)

@app.callback(
    Output('ticker-input', 'value'),
    [Input('update-ticker-btn', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def update_ticker(n_clicks, ticker):
    if n_clicks is not None and ticker:
        update_data_for_symbol(ticker)
    return ''


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=9999)
