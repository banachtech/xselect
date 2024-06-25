import sys
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
sys.path.append(base_dir)
financials_path = os.path.join(base_dir,'data', 'finance_data.db') 
fake_financials_path = os.path.join(base_dir,'data', 'financials.db') 
baskets_path = os.path.join(base_dir, 'data', 'baskets.db') 

# MC settings
SEED = 42
NUMPATHS = 10_000

# Datasets
PRICES_FILE = 'data/sp500_prices.csv'
FINANCIALS_FILE = 'data/sp500_overview.csv'
FEDFUNDS_FILE = 'data/fedfunds.csv'
FCN_BASKETS_FILE = 'data/fcn-baskets.csv'
MACRO_FILE = 'data/macro.csv'
FINANCIALS_DB_URL = f"sqlite:///{financials_path}"
FAKE_FINANCIALS_DB_URL = f"sqlite:///{fake_financials_path}"
BASKETS_DB_URL = f"sqlite:///{baskets_path}"

# Market data
RISK_FREE_RATE = 0.03
MIN_VOL = 0.05
VOL_SHIFT = -0.01
CORR_SHIFT = 0.05
MIN_CORR = 0.25
MAX_CORR = 0.95
CORR_WINDOW = 252

# COMMON CONTRACT PARAMETERS
FEES = 0.02
DAYS_PER_YEAR = 252
WEEKS_PER_YEAR = 52

# FCN default contract parameters
FCN_STRIKE = 0.8
FCN_COUPON_ANNUAL = 0.10
FCN_KO_BARRIER = 1.0
FCN_PERIODLEN = 0.25
FCN_NUMPERIODS = 4
FCN_AKI = 0.6
FCN_COUPON = FCN_COUPON_ANNUAL * FCN_PERIODLEN

# BCN default contract parameters
BCN_STRIKE = 0.8
BCN_PR = 1.0
BCN_COUPON_ANNUAL = 0.10
BCN_MATURITY = 1.0

# ACCU default contract parameters
ACCU_KO = 1.05
ACCU_STRIKE = 0.90
ACCU_LEVERAGE = 2
ACCU_SETTLEMENT_PERIOD = 5
ACCU_NUM_SETTLEMENTS = 26
ACCU_NUMSHARES = 1000

# BENCHMARK DATA
PCT_BENCHMARKS = ['SPY', 'GLD', 'IEF', 'SHY', 'TLT']
#AVG_BENCHMARKS = ['TSY3M', 'TSY10Y', 'TSY30Y', 'INFLATION']
AVG_BENCHMARKS = ['3month', '10year', '30year', 'inflation_rate']