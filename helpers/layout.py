from dash import dcc, html
import dash_bootstrap_components as dbc
import base64
import plotly.graph_objs as go

logo = base64.b64encode(open('../assets/logo.png', 'rb').read()).decode('utf-8')
banner = html.Header(
        html.Img(src=f'data:image/png;base64,{logo}', alt='Banner', height='60px'),
        style={'textAlign': 'center'}
)