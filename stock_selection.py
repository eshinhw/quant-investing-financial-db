import os
import json
import math
import price
import ratios
import requests
import momentum
import pyticker
import dividend
import numpy as np
import pandas as pd
import datetime as dt
import pandas_datareader.data as web

###############################################################################
# GLOBAL VARIABLES
WATCHLIST = ['O']
MOMENTUM_PERIODS = [3,6,12,24,36,48,60,72,84,96,108,120]
MARKET_CAP_THRESHOLD = 200
DIVIDEND_GROWTH_YRS_THRESHOLD = 10
DIVIDEND_GROWTH_RATE_THRESHOLD = 0.10
MOMENTUM_THRESHOLD = 1
###############################################################################

def extract_from_sp500():

    sp500 = pyticker.get_symbols_by_index('S&P 500')

    data = {'Symbol': [], 'Market_Cap (B)': []}

    min_market_cap = MARKET_CAP_THRESHOLD
    count = 0
    print("::::: EXTRACT SYMBOLS FROM S&P 500 :::::")
    for symbol in sp500:
        count += 1

        try:
            market_cap = ratios.calculate_market_cap(symbol)
        except:
            continue

        if market_cap >= min_market_cap and dividend.exists_dividends(symbol):
            data['Symbol'].append(symbol)
            data['Market_Cap (B)'].append(market_cap)
            print(f"{symbol}:\t{count}/{len(sp500)} => EXTRACTED!")
        else:
            print(f"{symbol}:\t{count}/{len(sp500)}")

    return data



def compare_symbol_list():
    new_data = extract_from_sp500()
    if not os.path.exists('./symbols_selected_from_sp500.json'):
        with open('./symbols_selected_from_sp500.json', 'w') as fp:
            json.dump(new_data,fp)
    else:
        with open('./symbols_selected_from_sp500.json', 'r') as fp:
            loaded_data = json.load(fp)
        if not (loaded_data == new_data):
            with open('./symbols_selected_from_sp500.json', 'w') as fp:
                json.dump(new_data,fp)


###############################################################################
# Load Data
###############################################################################
def construct_stock_df_to_csv():

    compare_symbol_list()

    with open('./symbols_selected_from_sp500.json', 'r') as fp:
        data = json.load(fp)
    df = pd.DataFrame(data)
    df.set_index('Symbol', inplace=True)

    ###############################################################################
    # Update Watchlist
    ###############################################################################
    watchlist_data = {'Symbol': [], 'Market_Cap (B)': []}
    print("::::: INSERT ADDITIONAL STOCKS FROM WATCHLIST :::::")
    count = 0
    for symbol in WATCHLIST:
        count += 1
        print(f"{symbol}:\t{count}/{len(WATCHLIST)}")
        if len(WATCHLIST) == 1:
            watchlist_data['Symbol'] = symbol
            watchlist_data['Market_Cap (B)'] = ratios.calculate_market_cap(symbol)
        else:
            watchlist_data['Symbol'].append(symbol)
            watchlist_data['Market_Cap (B)'].append(ratios.calculate_market_cap(symbol))

    df.reset_index(inplace=True)
    df = df.append(watchlist_data, ignore_index=True)
    df.set_index('Symbol', inplace=True)

    ###############################################################################
    # Financial Ratios Calculations
    ###############################################################################
    print("::::: CALCULATE FINANCIAL RATIOS :::::")
    count = 0
    for symbol in list(df.index):
        count += 1
        print(f"{symbol}:\t{count}/{len(list(df.index))}")
        try:
            div_growth = dividend.calcualte_avg_dividend_growth(symbol,DIVIDEND_GROWTH_YRS_THRESHOLD)
            df.loc[symbol, 'Dividend_Growth'] = div_growth
        except:
            df.loc[symbol, 'Dividend_Growth'] = np.nan

        try:
            div_yield = dividend.calculate_current_dividend_yield(symbol)
            df.loc[symbol, 'Dividend_Yield'] = div_yield
        except:
            df.loc[symbol, 'Dividend_Yield'] = np.nan

        try:
            mom = momentum.calculate_equal_weight_momentum(symbol, MOMENTUM_PERIODS)
            df.loc[symbol,'Momentum'] = mom
        except:
            df.loc[symbol,'Momentum'] = np.nan

    df.dropna(inplace=True)
    df = df[(df['Dividend_Growth'] >= DIVIDEND_GROWTH_RATE_THRESHOLD) & (df['Momentum'] >= MOMENTUM_THRESHOLD)]
    print('::::: FINAL DATAFRAME BEFORE EXPORT :::::')
    print(df)
    df.to_csv(r'./stock_selection.csv')

if __name__ == '__main__':
    construct_stock_df_to_csv()







