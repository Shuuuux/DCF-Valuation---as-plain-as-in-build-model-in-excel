# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 19:29:57 2023

@author: fsy

Utilizing Alpha Vantage for their Realtime & historical stock market data API,
to gather company financials.

NOTE: url request code taken directly from their documentation. https://www.alphavantage.co/documentation/. 

"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def visual_timeseries(symbol):
    """
    generating three stock price charts with time period 1 year, 6 month, 1 week, 
    showing high, low, close price
    
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey=demo'
    r = requests.get(url)
    data = r.json()
    
    #convert json to pandas dataframe    
    daily = data['Time Series (Daily)']
    df = pd.DataFrame.from_dict(daily, orient='index')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype({'Open': 'float', 'High': 'float', 'Low': 'float', 'Close': 'float', 'Volume': 'int'})
    df.index = pd.to_datetime(df.index)

    #get nearest date shown in API
    nearest_date = df.index[0]
    y1ago = pd.Timestamp(nearest_date.year - 1, nearest_date.month, nearest_date.day)
    m6ago = pd.Timestamp(nearest_date - timedelta(days=182))
    w1ago = pd.Timestamp(datetime.now() - timedelta(days=7))
    
    #three time period: 1 year, 6 month, 1 week
    daily_1y = df[df.index > y1ago]
    daily_6m = df[df.index > m6ago]
    daily_1w = df[df.index > w1ago]
    
    #create charts for three time period
    y1price = daily_1y[["High","Low","Close"]]
    chart1 = y1price.plot()
    m6price = daily_6m[["High","Low","Close"]]
    chart2 = m6price.plot()
    d7price = daily_1w[["High","Low","Close"]]
    chart3 = d7price.plot()
    
    return chart1,chart2,chart3


def visual_compare_histoyical(symbol, estimatedprice):
    """
    generating a bar chart to compare real price and estimated price at latest fiscal year end 
    """
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey=demo'
    r = requests.get(url)
    data = r.json()
    
    url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey=demo'
    r = requests.get(url)
    income = r.json()
    
    initial_date = income['annualReports'][0]['fiscalDateEnding']
    initial_date = pd.to_datetime(initial_date)
    formatted = initial_date.strftime('%d %B %Y')
 
    # format json to pandas
    daily = data['Time Series (Daily)']
    df = pd.DataFrame.from_dict(daily, orient='index')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype({'Open': 'float', 'High': 'float', 'Low': 'float', 'Close': 'float', 'Volume': 'int'})
    df.index = pd.to_datetime(df.index)
    
    # get real price at the certain day
    nearest_date = df.index.get_indexer([initial_date], method='nearest')[0]
    nearest_date = df.index[nearest_date]

    real_price = float(df.loc[nearest_date.strftime('%Y-%m-%d'), 'Close'])
    estimatedprice = float(estimatedprice)
    
    REAL = [real_price]
    ESTIMATE = [estimatedprice]
    
    width = 0.5
    pos = np.array(range(1))
    plt.clf()
    plt.bar(pos,REAL,width,color = 'blue', label = 'real price')
    plt.bar(pos + width + 0.1, ESTIMATE, width, color = 'grey', label = 'Estimated Price')
    
    plt.ylabel('USD ($)')
    plt.title(f'Comparasion on {formatted}')
    plt.show()
    




