import requests
import concurrent.futures
import os
import pandas as pd
import time
import sys

import sys
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
sys.path.append(base_dir)

from src.default_settings import *
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import func
# from voldata import calc_vols
# from baskets import calc_baskets


engine = create_engine(FINANCIALS_DB_URL)
Session = sessionmaker(bind=engine)

Base = declarative_base()

class CompanyOverview(Base):
    __tablename__ = 'company_overviews'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Symbol = Column(String, nullable=False)
    Name = Column(String)
    Description = Column(String)
    Currency = Column(String)
    Sector = Column(String)
    Industry = Column(String)
    LatestQuarter = Column(String)
    MarketCapitalization = Column(Float)
    PERatio = Column(Float)
    DividendYield = Column(Float)
    ProfitMargin = Column(Float)
    OperatingMargin = Column(Float)
    ReturnOnAssets = Column(Float)
    ReturnOnEquity = Column(Float)
    QuarterlyEarningsGrowthYOY = Column(Float)
    AnalystTargetPrice = Column(Float)
    AnalystRatingStrongBuy = Column(Integer)
    AnalystRatingBuy = Column(Integer)
    AnalystRatingHold = Column(Integer)
    AnalystRatingSell = Column(Integer)
    AnalystRatingStrongSell = Column(Integer)
    TrailingPE = Column(Float)
    ForwardPE = Column(Float)
    PriceToSalesRatio = Column(Float)
    PriceToBookRatio = Column(Float)
    EVToEBITDA = Column(Float)
    Beta = Column(Float)
    Week52High = Column(Float)
    Week52Low = Column(Float)
    Day50MovingAverage = Column(Float)
    Day200MovingAverage = Column(Float)

class HistoricalPrice(Base):
    __tablename__ = 'historical_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    adjusted_close = Column(Float, nullable=True)


class QuaterlyEarnings(Base):
    __tablename__ = 'quaterly_earnings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    fiscal_date_ending = Column(DateTime, nullable=False)
    reported_date = Column(DateTime, nullable=False)
    reported_eps = Column(Float)
    estimated_eps = Column(Float)
    surprise_percentage = Column(Float)

Base.metadata.create_all(engine)

url = "http://www.alphavantage.co/query"
load_dotenv()
apikey = os.getenv('ALPHAVANTAGE_API_KEY')
max_workers = os.cpu_count() * 2
_ov_items = ['Symbol', 'Name', 'Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter', 'MarketCapitalization', 'PERatio', 'DividendYield', 'ProfitMargin', 'OperatingMarginTTM', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM', 'QuarterlyEarningsGrowthYOY', 'AnalystTargetPrice', 'AnalystRatingStrongBuy', 'AnalystRatingBuy', 'AnalystRatingHold', 'AnalystRatingSell', 'AnalystRatingStrongSell', 'TrailingPE', 'ForwardPE', 'PriceToSalesRatioTTM', 'PriceToBookRatio', 'EVToEBITDA', 'Beta', '52WeekHigh', '52WeekLow', '50DayMovingAverage', '200DayMovingAverage']


# unused
def get_all_prices(symbols):
    res = []
    st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_prices, symbol): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            s = futures[future]
            try:
                tmp = future.result()
            except Exception as e:
                print(f'Error processing {s}: {e.__str__()}')
            else:
                res.append(tmp)
    ed = time.time() - st
    if res:
        print(f'{len(res)} symbols processed in {ed:0.2f} seconds')
        res = pd.concat(res, axis=1)
    else:
        res = pd.DataFrame()
    return res

def get_prices(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={apikey}&datatype=csv&outputsize=full'
    px = pd.read_csv(url, parse_dates=True, index_col='timestamp')
    px = px['adjusted_close']
    px.name = symbol
    px.sort_index(ascending=True, inplace=True)
    px.index = px.index.map(lambda x: int(x.timestamp()))
    if px.isnull().values.any():
        return None
    else:
        return px

def get_quaterly_earnings(symbol):
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={apikey}&datatype=json&outputsize=full'
    response = requests.get(url)
    data = response.json()
    
    quarterly_data = data['quarterlyEarnings']
    df = pd.json_normalize(quarterly_data)
    df['symbol'] = symbol
    
    df = df.rename(columns={
        'fiscalDateEnding': 'fiscal_date_ending',
        'reportedDate': 'reported_date',
        'reportedEPS': 'reported_eps',
        'estimatedEPS': 'estimated_eps',
        'surprisePercentage': 'surprise_percentage',
    })
    
    df['fiscal_date_ending'] = pd.to_datetime(df['fiscal_date_ending']).apply(lambda x: x.timestamp())
    df['reported_date'] = pd.to_datetime(df['reported_date']).apply(lambda x: x.timestamp())
    df = df.drop('surprise', axis=1)
    df = df.drop('reportTime', axis=1)
    return df

def check_if_exist(symbol, tmp):
    session = Session()
    latest_timestamp = session.query(func.max(HistoricalPrice.timestamp)).filter_by(symbol=symbol)
    
    session.close()
    # print(tmp['timestamp'])
    if tmp['timestamp'] > latest_timestamp:
        return True 
    else:
        return False


def get_prices_latest(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={apikey}&datatype=csv&outputsize=full'
    px = pd.read_csv(url, parse_dates=True, index_col='timestamp')
    px = px['adjusted_close']
    px.name = symbol
    px.sort_index(ascending=True, inplace=True)
    px.index = px.index.map(lambda x: int(x.timestamp()))
    # get the most recent price row
    most_recent_price = px.iloc[-1]
    most_recent_timestamp = px.index[-1]
    
    # Create a DataFrame with the most recent price, timestamp, and symbol
    data = {
        'timestamp': [most_recent_timestamp],
        'symbol': [symbol],
        'adjusted_close': [most_recent_price]
    }
    df = pd.DataFrame(data)
    
    return df

def get_current_quote(symbol):
    payload = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": apikey}
    r = requests.get(url, params=payload)
    r = r.json()["Global Quote"]["05. price"]
    return float(r)

def get_score(symbol, topics=None, limit=100):
    u = f'https://www.alphavantage.co/query'
    payload = {'function': 'NEWS_SENTIMENT', 'tickers': symbol, 'apikey':apikey, 'limit': limit}
    if not topics:
        if isinstance(topics, list):
            topics = ','.join(topics)
        payload.update({'topics': topics})
    r = requests.get(u, params=payload)
    r = r.json()['feed']
    scores = [float(x['relevance_score']) * float(x['ticker_sentiment_score']) for d in r for x in d['ticker_sentiment'] if x['ticker'] == symbol]
    if scores:
        return sum(scores)/len(scores)
    return None

def get_overview(symbol, items=_ov_items, none_values=["None", "-", "none","","null"]):
    payload = {"function": "OVERVIEW", "symbol": symbol, "apikey": apikey}
    r = requests.get(url, params=payload)
    r = r.json()
    df = pd.DataFrame([r]).replace(none_values, None)
    if items:
        df = df[items]
    string_cols = ['Symbol', 'Name', 'Description', 'Currency', 'Sector', 'Industry', 'LatestQuarter']
    for c in df.columns:
        if c not in string_cols:
            df[c] = pd.to_numeric(df[c])
    df = df.rename(
        columns={'OperatingMarginTTM': 'OperatingMargin', 
                 'ReturnOnAssetsTTM': 'ReturnOnAssets',
                 'ReturnOnEquityTTM': 'ReturnOnEquity',
                 'PriceToSalesRatioTTM': 'PriceToSalesRatio',
                 '52WeekHigh': 'Week52High', 
                 '52WeekLow':'Week52Low', 
                 '50DayMovingAverage': 'Day50MovingAverage', 
                 '200DayMovingAverage':'Day200MovingAverage',})
    # get current price and normalize dollar columns
    p = get_current_quote(symbol)
    dollar_cols = ['AnalystTargetPrice','Week52High','Week52Low','Day50MovingAverage','Day200MovingAverage']
    for c in dollar_cols:
        df[c] = df[c]/p
    return df

def get_latest_quarter(symbol):
    payload = {"function": "OVERVIEW", "symbol": symbol, "apikey": apikey}
    r = requests.get(url, params=payload)
    r = r.json()
    latest_quarter = r.get('LatestQuarter')

    if latest_quarter:
        latest_quarter_datetime = datetime.strptime(latest_quarter, '%Y-%m-%d')
        latest_quarter_timestamp = int(latest_quarter_datetime.timestamp())
        return latest_quarter_timestamp
    else:
        raise ValueError("LatestQuarter not found in the response")

def get_all_overviews(symbols):
    res = []
    st = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_overview, symbol): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            s = futures[future]
            try:
                tmp = future.result()
            except Exception as e:
                print(f'Error processing {s}: {e.__str__()}')
            else:
                res.append(tmp)
    ed = time.time() - st
    if res:
        print(f'{len(res)} symbols processed in {ed:0.2f} seconds')
        res = pd.concat(res, axis=0)
    else:
        res = pd.DataFrame()
    return res


def save_company_overview(df, engine):
    try:
        df.to_sql('company_overviews', con=engine, if_exists='append', index=False)
    except Exception as e:
        print(e)

def save_quaterly_earnings(df, engine):
    try:
        df.to_sql('quaterly_earnings', con=engine, if_exists='append', index=False)
    except Exception as e:
        print(e)
        
def save_historical_prices(df, engine):
    try:
        df.reset_index().melt(id_vars=['timestamp'], var_name='symbol', value_name='adjusted_close').rename(columns={'index': 'timestamp'}).to_sql('historical_prices', con=engine, if_exists='append', index=False)
    except Exception as e:
        print(e)

def save_historical_prices_latest(dfs, engine): 
    try:
        df = pd.concat(dfs, ignore_index=True)
        df.to_sql('historical_prices', con=engine, if_exists='append', index=False)
    except Exception as e:
        print(e)

def check_symbol(symbol):
    url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={symbol}&apikey={apikey}&datatype=csv&outputsize=full'
    px = pd.read_csv(url)
    if not px.empty:
        px = px.iloc[:,:2]
        return px 
    else:
        return False



def main(n: int):
    sp100 = pd.read_csv("../data/sp500-tickers.csv")
    symbols = sp100["Ticker"][:]

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
        save_company_overview(res, engine)

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
        #     # if NaN value does not exist in the dataframe then append
        #     # Question what should i do if the NaN value exists
        #     if tmp is not None:ps.append(tmp)
    ed = time.time() - st
    
    if ps:
        ps = pd.concat(ps, axis=1)
        print(f'{ps.shape[1]} symbols processed in {ed:0.2f} seconds')
        save_historical_prices(ps, engine)
    
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
        save_quaterly_earnings(res, engine)


def periodic(n):

    session = Session()
    sp500 = pd.read_csv("data/sp100_overview.csv")
    symbols = sp500["Ticker"][:n]
    # for each symbol in the database:
    for symbol in symbols:
        # get the latestquarter date in company overview for each symbol from the table
        result = session.query(CompanyOverview.LatestQuarter).filter_by(Symbol=symbol).order_by(CompanyOverview.id.desc()).first()
        session.close()

        if result and result.LatestQuarter:
            try:
                latest_quarter_dt = datetime.strptime(result.LatestQuarter, '%Y-%m-%d')
                latest_quarter_unix = int(latest_quarter_dt.timestamp())

            except ValueError as e:
                print(f"Error parsing date: {e}")
        else:
            print(f"No data found for symbol {symbol}")

        # for every ticker in the database, check the corresponding latestquarter date from api
        current_latest_quarter = get_latest_quarter(symbol)

        # if the date is not equal the current date:
        if current_latest_quarter != latest_quarter_unix:
            # reupdate the ticker overview
            print('need to reupdate')
            res = []
            try:
                tmp = get_overview(symbol)
            except Exception as e:
                print(f'skipped symbol {symbol}')
                print(e)
            else:
                res.append(tmp)
                break
    
            if res:
                res = pd.concat(res, axis=0)
                save_company_overview(res, engine)


        # download new historical stock prices
            # update database with new prices
    ps = []
    for symbol in symbols:
        try:
            tmp = get_prices_latest(symbol)
        except Exception as e:
            print(f'skipped symbol {symbol}')
        else:
            # check if the date in the dataframe is greater than the latest date in the database
            # for the given symbol
            exist = check_if_exist(symbol, tmp)
            print(exist)
            if exist: ps.append(tmp)
    
    if ps:
        save_historical_prices_latest(ps, engine)
        print("appended latest prices")   

        # download new fed funds rate # default is monthly
            # download the new fed funds rate and update the database

if __name__ == "__main__":

    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        m = sys.argv[2]
    else:
        n = 100
        m = 'once'
    
    # IF running this for the first time
    if m == 'once':
        main(n)

    # IF running this periodically
    if m == 'periodic':
        periodic(n)