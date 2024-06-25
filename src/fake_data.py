import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

FINANCIALS_DB_URL = 'sqlite:///data/financials.db'  

engine = create_engine(FINANCIALS_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

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
    DateAppend = Column(Date)

Base.metadata.create_all(engine)

original_array = [3180062310000.0, 37.01, 0.007, 0.364, 0.446, 0.154, 0.385, 0.2, 1.0391744476287326, 23, 32, 3, 0, 0, 37.01, 31.95, 13.44, 12.57, 24.9, 0.893, 1.0021262827031525, 0.7111491171304428, 0.9617962466487935, 0.8828464454100028]
fixed_values = ('MSFT', 'Microsoft Corporation', "Microsoft Corporation is an American multinational technology company which produces computer software, consumer electronics, personal computers, and related services. Its best known software products are the Microsoft Windows line of operating systems, the Microsoft Office suite, and the Internet Explorer and Edge web browsers. Its flagship hardware products are the Xbox video game consoles and the Microsoft Surface lineup of touchscreen personal computers. Microsoft ranked No. 21 in the 2020 Fortune 500 rankings of the largest United States corporations by total revenue; it was the world's largest software maker by revenue as of 2016. It is considered one of the Big Five companies in the U.S. information technology industry, along with Google, Apple, Amazon, and Facebook.", 'USD', 'TECHNOLOGY', 'SERVICES-PREPACKAGED SOFTWARE', '2024-03-31')

def generate_random_arrays(original, num_arrays=500, deviation=0.9):
    original = np.array(original)
    arrays = []
    for _ in range(num_arrays):
        random_array = original * (1 + deviation * (np.random.rand(len(original)) * 2 - 1))
        arrays.append(random_array.tolist())
    return arrays

random_arrays = generate_random_arrays(original_array)

start_date = datetime.now()

for i, array in enumerate(random_arrays):
    current_date = start_date + timedelta(weeks=2 * i)
    company_overview = CompanyOverview(
        Symbol=fixed_values[0],
        Name=fixed_values[1],
        Description=fixed_values[2],
        Currency=fixed_values[3],
        Sector=fixed_values[4],
        Industry=fixed_values[5],
        LatestQuarter=fixed_values[6],
        MarketCapitalization=array[0],
        PERatio=array[1],
        DividendYield=array[2],
        ProfitMargin=array[3],
        OperatingMargin=array[4],
        ReturnOnAssets=array[5],
        ReturnOnEquity=array[6],
        QuarterlyEarningsGrowthYOY=array[7],
        AnalystTargetPrice=array[8],
        AnalystRatingStrongBuy=int(array[9]),
        AnalystRatingBuy=int(array[10]),
        AnalystRatingHold=int(array[11]),
        AnalystRatingSell=int(array[12]),
        AnalystRatingStrongSell=int(array[13]),
        TrailingPE=array[14],
        ForwardPE=array[15],
        PriceToSalesRatio=array[16],
        PriceToBookRatio=array[17],
        EVToEBITDA=array[18],
        Beta=array[19],
        Week52High=array[20],
        Week52Low=array[21],
        Day50MovingAverage=array[22],
        Day200MovingAverage=array[23],
        DateAppend=current_date.date()
    )
    session.add(company_overview)

session.commit()

session.close()