# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 19:26:37 2023
@author: Shuyu Fang
description: Use DCF modeling to calculate stock price and present the model and some output charts
 
future goals: 
    -- Develop isolated Discounted Cash Flow functions to enhance the readability 
	-- Construct a graph to compare actual versus estimated stock prices over different time intervals
	-- Devise a script to find out an appropriate assumed growth rate for a company
	-- Formalize sensitivity analysis

"""
# cell 1
# set & check current working directory
import os
script_path = os.path.abspath(__file__)
print("Your script path:", script_path)

directory = os.path.dirname(os.path.abspath(script_path))
os.chdir(directory)

#check
current_WD = os.getcwd()
print(f'Your currenct working directory: {current_WD}')

#%% cell 2

import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import numpy as np
from plot import * 
"""
    please input the stock code (eg, SBUX, IBM, GOOGL)
    Then you will get several intuitive stock price movement chards for the most recent dates which the API provides
"""
symbol = input("Enter the stock code: ")
symbol = str(symbol).upper()
df = pd.read_csv('listing_status.csv')
find = df.symbol.isin([symbol])

# Check if the column with the given stock code exists
if find.any():
    print('your stock code is right, please continue')
else:
    print('Wrong stock code, please check the listing_status.csv file')


# please continue to cell 2
#%%% cell 3


print(visual_timeseries(symbol))


"""
    step 1: get data

    Utilizing Alpha Vantage for their Realtime & historical stock market data API, to gather company financials.
    NOTE: url request taken directly from their documentation. https://www.alphavantage.co/documentation/
    
    Key Variable explanation:
    funda : company fundamental information in json
    income: income statement in json
    balance: balance sheet in json
    cash: cash flow in json
    Tyield: 10-year Treasury Yield in json

"""
# access to company fundamental information
url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey=demo'
r = requests.get(url)
funda = r.json()

# access to Income statement
url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey=demo'
r = requests.get(url)
income = r.json()

# access to balance sheet
url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey=demo'
r = requests.get(url)
balance = r.json()

#access to cash flow 
url = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey=demo'
r = requests.get(url)
cash = r.json()

##  access to 10-year Treasury Yield
url = 'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey=demo'
r = requests.get(url)
Tyield = r.json()


"""
    step 2: DCF modeling 

    2.1 preparation work : 
    extract key information from financial statements, store each variable with a numpy list

    Key Variable explanation:
    
    first_date = the nearest date to today in the income statement
    FYS: five financial year-end dates in a list (different company has different dates)
    GPROFIT: past 5-year gross profit
    TR: past 5-year total revenue
    OExp: past 5-year operating expenses
    DA: past 5-year depreciation and amortization
    EBITDA: past 5-year EBITDA
    
    cash flow
    OCF: past 5-year operating cash flow
    CAPEX: past 5-year capital expenditures
"""
# i. get five financial year end dates in a list
first_date = income['annualReports'][0]['fiscalDateEnding']
first_date = datetime.strptime(first_date, "%Y-%m-%d")
FYS = [str(datetime(first_date.year - i, first_date.month, first_date.day).date()) for i in range(5)]
FY5, FY4, FY3, FY2, FY1 = FYS

# ii. get key data in np.array format
#income statement
GPROFIT = np.array([]) 
TR = np.array([]) 
OExp = np.array([]) 
DA = np.array([]) 
EBITDA = np.array([]) 

for report in income['annualReports']:
    for i in range(len(FYS)):
        if report['fiscalDateEnding'] == FYS[i]:
            gP = float(report['grossProfit'])
            tR = float(report["totalRevenue"])
            oE = float(report["operatingExpenses"])
            dA = float(report["depreciationAndAmortization"])
            ebitda = float(report["ebitda"])
            GPROFIT = np.append(GPROFIT, gP)
            TR = np.append(TR, tR)
            OExp = np.append(OExp, oE)
            DA = np.append(DA, dA)
            EBITDA = np.append(EBITDA, ebitda)
 
# cash flow          
OCF = np.array([]) 
CAPEX = np.array([]) 

for report in cash['annualReports']:
    for i in range(len(FYS)):
        if report['fiscalDateEnding'] == FYS[i]:
            ocf = float(report['operatingCashflow'])
            capex = float(report["capitalExpenditures"])
            OCF = np.append(OCF, ocf)
            CAPEX = np.append(CAPEX, capex)           


"""
    2.2 process to get estimated 5-year unleveraged free cash flow
    
    Key Variable explanation:
    1) g_revenue : CAGR of total revenue, here as assumed growth rate
    2) etr: estimated 5-year total revenue
    3) egp: estimated 5-year gross profit
    4) eopex: estimate 5-year operating expenses
    5) eebit: estimate 5-year EBIT
    6) eda: estimate 5-year D&A
    7) eebitda: estimate 5-year EBITDA
    8) efcf: estimated unleveraged free cash flow
"""
# 1) g_revenue: CAGR method
g_revenue = ((TR[0] / TR[4]) ** (1/4)) - 1 #FY5 total revenue/FY1 total revenue

# 2) etr
E_FY = np.arange(6,11) # Estimated Fiscal Year  
etr = np.zeros(len(E_FY)) 
etr[0] = TR[0] * (1 + g_revenue)  

for i in range(1, len(E_FY)):
    etr[i] = etr[i - 1] * (1 + g_revenue) 

# 3) egp: get average gross profit margin, then plus by etr
GP_margin = GPROFIT / TR 
gp_margin = np.average(GP_margin) 
egp = etr * gp_margin 

# 4) eopex: get average operating expense margin, then plus by etr
OExp_margin = OExp / TR
oexp_margin = np.average(OExp_margin)
eopex = etr * oexp_margin 

# 5) eebit
eebit = egp - eopex

# 6) eda : get average D&A margin, then plus by etr
DA_margin = DA / TR
da_margin = np.average(DA_margin)
eda = etr * da_margin

# 7) eebita 
eebitda = eebit + eda

# 8) efcf: get past 5-year free cash flow first, then get FCF/EBITDA ratio, plus by eebitda
FCF = OCF - CAPEX #past 5-year free cash flow
RATE = FCF / EBITDA	
rate = np.average(RATE)
efcf = eebitda * rate


""" 
    step 3: WACC calculation
    
    3.1 get effective tax rate
    
    Key Variable explanation:
    effective_tax_rate: effective tax rate
"""
# 3.1 effective tax rate  
for report in income['annualReports']:
    if report['fiscalDateEnding'] == FYS[0]:
       income_before_tax = float(report["incomeBeforeTax"])
       tax_expense = float(report["incomeTaxExpense"])
       break

effective_tax_rate = (tax_expense / income_before_tax)


"""
    3.2 utilize CAPM to calculate the cost of equity
    1) web scrapping the market return
    2) get beta from company fundamental information
    3) get risk free rate
    4) cost of equity calculation
    
    Key Variable explanation:
    mktreturn: market return (5-year average S&P500 return)
    beta : beta in CAPM
    risk_free_rate: Ten-year Treasury Yield at nearest FY end date
"""
# 1) web scrapping the market return
url = 'https://tradethatswing.com/average-historical-stock-market-returns-for-sp-500-5-year-up-to-150-year-averages/'
req = requests.get(url)

soup = BeautifulSoup(req.text, 'lxml')
tabs = soup.find_all('table')
tab = tabs[0]
rows = tab.findAll('tr')

for row in rows:
    cols = row.findAll("td")

for row in rows[7:8]:
    cols = row.findAll("td")
    mktreturn = cols[1].get_text()
    
mktreturn = float(mktreturn.strip('%'))/100

# 2) get beta from company fudamental information
beta = float(funda['Beta'])

# 3) get risk free rate
tday = str(datetime(first_date.year, first_date.month, 1).date())
for entry in Tyield['data']:
    if entry["date"] == tday:
        risk_free_rate = float(entry["value"]) / 100     

# 4) cost of equity calculation (CAPM)
cost_of_equity = risk_free_rate + beta * (mktreturn - risk_free_rate)


""" 
    3.3 calculate cost of debt
    1) get interest expense of two years
    2) get the total debt of two years
    3) calculate the cost of debt
    
    Key Variable explanation:
    avg_interest_expense: average interest expense
    avg_total_debt: average total debt
    cost_of_debt: cost of debt
"""
# 3.1 get interest expense of two years
for report in income['annualReports']:
    if report['fiscalDateEnding'] == FYS[0]:
        interest_expense1 = float(report['interestAndDebtExpense'])
    elif report['fiscalDateEnding'] == FYS[1]:
        interest_expense2 = float(report['interestAndDebtExpense'])

avg_interest_expense = (interest_expense1+interest_expense2)/2

# 3.2 get total debt of two years
for report in balance['annualReports']:
    if report['fiscalDateEnding'] == FYS[0]:
        totaldebt1 = float(report['shortLongTermDebtTotal'])
    elif report['fiscalDateEnding'] == FYS[1]:
        totaldebt2 = float(report['shortLongTermDebtTotal'])
        
avg_total_debt = (totaldebt1 + totaldebt1)/2

# 3.3 cost of debt
cost_of_debt = (avg_interest_expense / avg_total_debt)/(1 - effective_tax_rate)

 
""" 
    3.4 proportion of equity market cap / debt
    
    Key variables explanation:
    EMV: Equity market value
    p_E: Equity / (Equity + Debt)
    p_D: Debt / (Equity + Debt)
"""
EMV = float(funda['MarketCapitalization'])     
EMVanddebt = EMV + totaldebt1
p_E = EMV / EMVanddebt
p_D = totaldebt1 / EMVanddebt


""" 
    3.5 WACC
    
    Key Variable explanation:
    WACC : weighted average cost of capital (discount rate)
"""
WACC = cost_of_equity * p_E + cost_of_debt * p_D * (1 - effective_tax_rate)
WACC


""" 
    step 4: stock price estimation
    
    Key Variable explanation:
    1) g: Perpetual growth rate(long term GDP growth rate)
    2) sum_pv_ufcf: pv of estimated unleveraged free cash flow
    3) pv_Terminal: Terminal Value = FCF(n+1) / (WACC-growth rate)
    4) IEV: implied Enterprise Value
    5) net_debt: net debt
    6) PV_mktcap: Implied Equity Value(Market Cap)
    7) share_outstanding: shareout standing
    8) Estockprice: estimated stock price
"""

# 1) g: get from https://ycharts.com/indicators/us_real_gdp_growth - basic info
g = 0.03

# 2) sum_pv_ufcf
exp = np.arange(1,6)
pv_ufcf = efcf/((1 + WACC) ** exp)
sum_pv_ufcf = np.sum(pv_ufcf)

# 3) pv_Terminal (Terminal Value = FCF(n+1) / (WACC-growth rate))
Terminal = (pv_ufcf[4] * (1 + g)) / (WACC - g)
pv_Terminal = Terminal / ((1 + WACC) ** 5)

# 4) implied Enterprise Value
IEV = pv_Terminal + sum_pv_ufcf

# 5) net debt
for report in balance['annualReports']:
    if report['fiscalDateEnding'] == FYS[0]:
        cash_Equi = float(report['cashAndCashEquivalentsAtCarryingValue'])

net_debt = totaldebt1 - cash_Equi

# 6) Implied Equity Value(Market Cap)
PV_mktcap = IEV - net_debt

# 7) shares numbers
share_outstanding = int(funda['SharesOutstanding'])

# 8) estimated stock price
Estockprice = PV_mktcap / share_outstanding

#%% cell 4
"""
    OUTPUT
    1. FCF model 
    2. key variable value 
    3. estimated & real price comparasion chart
"""
# 1. display FCF model with pandas data frame 
df = pd.DataFrame([etr, egp, eopex, eebit, eda, eebitda, efcf],
                  index = ['TotalRevenue', 'GrossProfit', 'OperatingExpense', 
                         'EBIT', 'D&A', 'EBITDA', 'UnleveragedFCF'])

df /= 10 ** 6
df = df.astype({col: 'int' for col in df.select_dtypes('float').columns})
df.columns = ['EFY6', 'EFY7', 'EFY8', 'EFY9', 'EFY10']
print(df)

# 2. key variable value
df = pd.DataFrame([g, WACC, pv_Terminal, IEV, PV_mktcap, Estockprice],
                  index = ['Perpetual growth rate','WACC','Terminal Value','implied Enterprise Value',
                           'Implied Equity Value','estimated stock price'])

df.iloc[0:2] = df.iloc[0:2].applymap(lambda x: "{:.2%}".format(x))
df.iloc[2:5] = df.iloc[2:5] / 10 ** 6
df.iloc[2:5] = df.iloc[2:5].applymap(lambda x: "{}$m".format(int(x)))
df.iloc[-1] = df.iloc[-1].astype(float)
df.columns = ['value']
print(df)



# 3. estimated & real price comparasion chart
visual_compare_histoyical(symbol, Estockprice)

