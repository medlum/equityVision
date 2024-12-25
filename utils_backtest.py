import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ta.trend import MACD
from ta.momentum import RSIIndicator


# Define strategy parameters and their default states
strategy_params = {
    "Moving Average Crossover": {
        "sma_period": {"min_value": 1, "value": 50},
        "ema_period": {"min_value": 1, "value": 20},
        "period_select": {
            "sma period (days)": None,
            "ema period (days)": None
        }
    },
    "Bollinger Bands": {
        "bb_period": {"min_value": 1, "value": 20},
        "bb_std": {"min_value": 0.01, "value": 2.0},
        "period_select": {
            "Bollinger Bands Period (days)": None,
            "Bollinger Bands Standard Deviations" : None,
        }

    },
    "MACD": {
        "macd_fast": {"min_value": 1, "value": 12},
        "macd_slow": {"min_value": 1, "value": 26},
        "macd_signal": {"min_value": 1, "value": 9},
        "period_select": {
            "MACD Fast Period (days)": None,
            "MACD Slow Period (days)" : None,
            "MACD Signal Period (days)" : None
        }
    },
    
    "RSI": {
        "rsi_period": {"min_value": 1, "value": 14},
        "period_select": {"RSI Period (days)": None,}
    },

}

# define trading strategy
trading_strategy = ["Moving Average Crossover", 
                    "Bollinger Bands", 
                    "MACD", 
                    "RSI", 
                    ""]

def fetch_stock_data(ticker, 
                     period, 
                     sma_period, 
                     ema_period, 
                     bb_period, 
                     bb_std, 
                     macd_fast, 
                     macd_slow, 
                     macd_signal, 
                     rsi_period, 
                     strategy):
    
    # Fetch the stock data using yfinance
    stock_data = yf.Ticker(ticker)
    hist = stock_data.history(period=period)

    # Check if the fetched data is empty
    if hist.empty:
        st.error(f"No data found for {ticker} over the specified period.")
        return None, None

    # Initialize signals and positions
    hist['Signal'] = 0.0
    hist['Position'] = 0.0

    # "Moving Average Crossover
    if strategy == trading_strategy[0]:
        if sma_period is None or ema_period is None:
            st.error(
                "SMA and EMA periods must be specified for Moving Average Crossover.")
            return None, None

        hist['SMA'] = hist['Close'].rolling(window=sma_period).mean()
        hist['EMA'] = hist['Close'].ewm(span=ema_period, adjust=False).mean()

        if len(hist) < max(sma_period, ema_period):
            st.error(
                f"Not enough data to calculate {sma_period}-day SMA or {ema_period}-day EMA for {ticker}.")
            return None, None

        hist.loc[hist.index[sma_period:], 'Signal'] = np.where(
            hist.loc[hist.index[sma_period:], 'EMA'] > hist.loc[hist.index[sma_period:], 'SMA'], 1.0, 0.0)
        hist['Position'] = hist['Signal'].diff()
    
    #Bollinger Bands
    elif strategy == trading_strategy[1]:
        if bb_period is None or bb_std is None:
            st.error(
                "Bollinger Bands period and standard deviations must be specified.")
            return None, None

        hist['Middle_Band'] = hist['Close'].rolling(window=bb_period).mean()
        hist['Upper_Band'] = hist['Middle_Band'] + \
            (hist['Close'].rolling(window=bb_period).std() * bb_std)
        hist['Lower_Band'] = hist['Middle_Band'] - \
            (hist['Close'].rolling(window=bb_period).std() * bb_std)

        hist.loc[hist['Close'] < hist['Lower_Band'], 'Signal'] = 1.0
        hist.loc[hist['Close'] > hist['Upper_Band'], 'Signal'] = -1.0
        hist['Position'] = hist['Signal'].diff()

    # MACD
    elif strategy == trading_strategy[2]:
        if macd_fast is None or macd_slow is None or macd_signal is None:
            st.error("MACD fast, slow, and signal periods must be specified.")
            return None, None

        macd_indicator = MACD(hist['Close'], window_slow=macd_slow,
                              window_fast=macd_fast, window_sign=macd_signal)
        hist['MACD'] = macd_indicator.macd()
        hist['Signal_Line'] = macd_indicator.macd_signal()
        hist['MACD_Histogram'] = macd_indicator.macd_diff()

        hist['Signal'][hist['MACD'] > hist['Signal_Line']] = 1.0
        hist['Signal'][hist['MACD'] < hist['Signal_Line']] = -1.0
        hist['Position'] = hist['Signal'].diff()

    # RSI
    elif strategy == trading_strategy[3]:
        if rsi_period is None:
            st.error("RSI period must be specified.")
            return None, None

        rsi_indicator = RSIIndicator(hist['Close'], window=rsi_period)
        hist['RSI'] = rsi_indicator.rsi()

        hist['Signal'][hist['RSI'] < 30] = 1.0
        hist['Signal'][hist['RSI'] > 70] = -1.0
        hist['Position'] = hist['Signal'].diff()

    else:
        st.error("Invalid strategy selected.")
        return None, None

    return hist, strategy


@st.cache_data
def fetch_dividends(ticker):
    # Fetch the stock data
    stock = yf.Ticker(ticker)

    # Fetch historical dividends
    dividends = stock.dividends

    if dividends.empty:
        st.warning("No dividend data available.")
        return None
    else:
        # Create a DataFrame for dividends
        dividends_df = dividends.reset_index()
        dividends_df.columns = ['Date', 'Dividend']
        return dividends_df


# Function to backtest the strategy
@st.cache_data
def backtest_strategy(hist, strategy):
    # Calculate daily returns
    hist['Returns'] = hist['Close'].pct_change()
    # Calculate strategy returns by multiplying daily returns by the previous day's signal
    hist['Strategy_Returns'] = hist['Returns'] * hist['Signal'].shift(1)
    # Calculate cumulative returns for the strategy
    hist['Cumulative_Returns'] = (1 + hist['Strategy_Returns']).cumprod()
    # Calculate cumulative returns for the benchmark (buy and hold)
    hist['Cumulative_Benchmark_Returns'] = (1 + hist['Returns']).cumprod()

    # Calculate performance metrics
    total_return = hist['Cumulative_Returns'].iloc[-1] - 1
    benchmark_return = hist['Cumulative_Benchmark_Returns'].iloc[-1] - 1
    num_trades = hist['Position'].abs().sum() / 2
    win_rate = (hist['Strategy_Returns'] > 0).sum() / \
               (hist['Strategy_Returns'] != 0).sum()
    avg_profit = hist[hist['Strategy_Returns'] > 0]['Strategy_Returns'].mean()
    avg_loss = hist[hist['Strategy_Returns'] < 0]['Strategy_Returns'].mean()



    # Create a dictionary to store performance metrics
    performance_metrics = f"""

        :blue[**{strategy} Backtest Results**]

        **Total Return : {total_return:.2%}**. It represents the percentage increase or decrease in the value of the investment from the start to the end of the period.

        **Benchmark Return : {benchmark_return:.2%}**, which in this case is the closing price of the stock without any strategy. It serves as a reference point to compare the performance of the strategy against simply holding the stock.

        **Total Trades : {int(num_trades)}**.  It includes both buy and sell actions taken executed during the backtest.

        **Win Rate : {win_rate:.2%}**. It indicates how often :blue[{strategy}] strategy made a profit.

        **Average Profit : {avg_profit:.2%}**. It provides insight into the typical profit generated by successful trades.

        **Average Loss per Trade: {avg_loss:.2%}**. Average loss incurred on losing trades. It helps to understand the typical loss experienced by unsuccessful trades."""

    return hist, performance_metrics


# Function to fetch pre-calculated financial ratios
# @st.cache_data
def fetch_financial_ratios(ticker):
    # Fetch the stock data
    stock = yf.Ticker(ticker)

    # Get the info dictionary
    info = stock.info

    # Check if data is available
    if not info:
        st.error("No financial data available for the given ticker symbol.")
        return None

    # Define the ratios we want to fetch
    required_ratios = {
        'Previous Close': 'previousClose',
        'Open': 'open',
        'Volume': 'volume',
        'EPS': 'trailingEps',
        'Trailing P/E': 'trailingPE',
        'Forward P/E': 'forwardPE',
        'Price/Sales': 'priceToSalesTrailing12Months',
        'Price/Book': 'priceToBook',
        'EBITDA': 'ebitda',
        '1Y Target Est': 'targetMeanPrice',
        'Latest Dividend': 'dividendRate',  # New: Latest Dividend

    }

    # Fetch the ratios
    ratios = {}
    for ratio_name, info_key in required_ratios.items():
        if info_key in info:
            if info_key == 'volume':
                # Convert volume to millions
                ratios[ratio_name] = info[info_key] / 1_000_000
            elif info_key == 'ebitda' or info_key == 'marketCap':
                # Convert EBITDA and Market Cap to billions
                ratios[ratio_name] = info[info_key] / 1_000_000_000
            else:
                ratios[ratio_name] = info[info_key]
        else:
            st.toast(f"Data for {ratio_name} is not available.", icon="🚨")

    # Get the market cap and convert it to billions
    market_cap = info.get('marketCap', 'N/A')
    if market_cap != 'N/A':
        market_cap_in_billions = market_cap / 1_000_000_000
        ratios['Market Cap (in billions)'] = market_cap_in_billions
    else:
        ratios['Market Cap (in billions)'] = 'N/A'

    return pd.DataFrame([ratios]).melt(var_name="Metric", value_name="Value")


@st.cache_data
def plot_strategy(hist, ticker, strategy, sma_period=None, ema_period=None, bb_period=None, bb_std=None):
    if hist is None:
        return
    
    plt.figure(figsize=(10, 5))

    # "Moving Average Crossover
    if strategy == trading_strategy[0]:
        plt.plot(hist['Close'], label=f'{ticker} - Close Price', alpha=0.5)
        plt.plot(
            hist['SMA'], label=f'{ticker} - {sma_period}-day SMA', alpha=0.75)
        plt.plot(
            hist['EMA'], label=f'{ticker} - {ema_period}-day EMA', alpha=0.75)
        plt.plot(hist[hist['Position'] == 1].index, hist['EMA'][hist['Position'] == 1],
                 '^', markersize=10, color='g', lw=0, label=f'{ticker} - Buy Signal')
        plt.plot(hist[hist['Position'] == -1].index, hist['EMA'][hist['Position'] == -1],
                 'v', markersize=10, color='r', lw=0, label=f'{ticker} - Sell Signal')

    #Bollinger Bands
    elif strategy == trading_strategy[1]:
        plt.plot(hist['Close'], label=f'{ticker} - Close Price', alpha=0.5)
        plt.plot(hist['Middle_Band'],
                 label=f'{ticker} - {bb_period}-day Middle Band', alpha=0.75)
        plt.plot(hist['Upper_Band'],
                 label=f'{ticker} - Upper Band', alpha=0.75)
        plt.plot(hist['Lower_Band'],
                 label=f'{ticker} - Lower Band', alpha=0.75)
        plt.plot(hist[hist['Position'] == 1].index, hist['Lower_Band'][hist['Position'] == 1],
                 '^', markersize=10, color='g', lw=0, label=f'{ticker} - Buy Signal')
        plt.plot(hist[hist['Position'] == -1].index, hist['Upper_Band'][hist['Position'] == -1],
                 'v', markersize=10, color='r', lw=0, label=f'{ticker} - Sell Signal')

     # MACD
    elif strategy == trading_strategy[2]:
        plt.plot(hist['MACD'], label=f'{ticker} - MACD Line', alpha=0.75)
        plt.plot(hist['Signal_Line'],
                 label=f'{ticker} - Signal Line', alpha=0.75)
        plt.bar(hist.index, hist['MACD_Histogram'],
                label=f'{ticker} - MACD Histogram', color='purple', alpha=0.5)

    
    # RSI
    elif strategy == trading_strategy[3]:
        plt.plot(hist['RSI'], label=f'{ticker} - RSI', alpha=0.75)
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.plot(hist[hist['Position'] == 1].index, hist['RSI'][hist['Position'] == 1],
                 '^', markersize=10, color='g', lw=0, label=f'{ticker} - Buy Signal')
        plt.plot(hist[hist['Position'] == -1].index, hist['RSI'][hist['Position'] == -1],
                 'v', markersize=10, color='r', lw=0, label=f'{ticker} - Sell Signal')

    plt.title(f'{ticker} - {strategy} Strategy')
    plt.legend()
    st.pyplot(plt)

@st.cache_data
def plot_dividends(dividends_df, ticker):
    if dividends_df is None:
        return

    # Create a plot using Matplotlib
    plt.figure(figsize=(10, 5))
    plt.plot(dividends_df['Date'],
             dividends_df['Dividend'], linestyle='-')
    plt.title(f'Dividends History for {ticker}')
    plt.xlabel('Date')
    plt.ylabel('Dividend Amount ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)


@st.cache_data
def plot_backtest_results(hist, ticker):
    # Plot cumulative returns
    plt.figure(figsize=(10, 5))
    plt.plot(hist['Cumulative_Returns'],
             label=f'{ticker} - Strategy Cumulative Returns', alpha=0.75)
    plt.plot(hist['Cumulative_Benchmark_Returns'],
             label=f'{ticker} - Benchmark Cumulative Returns', alpha=0.75)
    plt.title(f'{ticker} - Cumulative Returns')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.legend()
    st.pyplot(plt)






