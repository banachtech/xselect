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

# connect to db
eng1 = create_engine(FINANCIALS_DB_URL)

overview = pd.read_sql("SELECT * FROM company_overviews", con=eng1)

prices = pd.read_sql("SELECT * FROM historical_prices", con=eng1, parse_dates=['timestamp']) # format the dataframe so symbols are columns
prices = prices.pivot(index='timestamp', columns='symbol', values='adjusted_close')

quaterly_earnings = pd.read_sql("SELECT * FROM quaterly_earnings", con=eng1)