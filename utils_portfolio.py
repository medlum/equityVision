import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date


# Function to update portfolio summary
def update_portfolio_summary():
    buy_df = st.session_state.buy_transactions
    sell_df = st.session_state.sell_transactions

    summary = []
    tickers = set(buy_df['Ticker']).union(sell_df['Ticker'])
    for ticker in tickers:
        buy_data = buy_df[buy_df['Ticker'] == ticker]
        sell_data = sell_df[sell_df['Ticker'] == ticker]

        total_bought = buy_data['Quantity'].sum()
        total_sold = -sell_data['Quantity'].sum()  # Convert sell quantity to negative
        balance_quantity = total_bought - total_sold  # Adjusted for negative sell quantity

        avg_buy_price = (buy_data['Quantity'] * buy_data['Buy Price']).sum() / total_bought if total_bought > 0 else 0

        # Fetch the latest price
        try:
            last_close_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
        except:
            last_close_price = 0  # Fallback if data unavailable

        unrealized_pnl = balance_quantity * (last_close_price - avg_buy_price) if balance_quantity > 0 else 0
        realized_pnl = (-sell_data['Quantity'] * (sell_data['Sell Price'] - avg_buy_price)).sum() if not sell_data.empty else 0  # Adjusted for negative sell quantity

        # Calculate total dividends
        ticker_obj = yf.Ticker(ticker)
        dividends = ticker_obj.dividends

        # Ensure index is DatetimeIndex and remove timezone if present
        if not dividends.empty and isinstance(dividends.index, pd.DatetimeIndex):
            if dividends.index.tz is not None:
                dividends.index = dividends.index.tz_localize(None)

            total_dividends = 0.0
            for index, row in buy_data.iterrows():
                buy_date = pd.Timestamp(row['Buy Date'])
                sell_date = datetime.now()

                sell_transaction = sell_data[
                    (sell_data['Quantity'] == -row['Quantity']) &
                    (pd.to_datetime(sell_data['Sell Date']) > buy_date)
                ]
                if not sell_transaction.empty:
                    sell_date = pd.Timestamp(sell_transaction['Sell Date'].iloc[0])

                quantity = row['Quantity']

                # ✅ Safe filtering
                filtered_dividends = dividends[
                    (dividends.index >= buy_date) & (dividends.index < sell_date)
                ]

        total_dividends += filtered_dividends.sum() * quantity
else:
    total_dividends = 0.0


        total_return = ((realized_pnl + unrealized_pnl + total_dividends) / (avg_buy_price * total_bought)) * 100 if total_bought > 0 else 0

        # Fetch industry information
        try:
            industry = ticker_obj.info.get('industry', 'N/A')
        except:
            industry = 'N/A'  # Fallback if data unavailable

         # Fetch stock exchange information
        stock_exchange = buy_data['Stock Exchange'].iloc[0] if not buy_data.empty else 'N/A'

           # Calculate total investment by stock exchange
        total_investment_by_exchange = buy_df.groupby('Stock Exchange').apply(
            lambda x: (x['Quantity'] * x['Buy Price']).sum()).reset_index(name='Total Investment')
        st.session_state.total_investment_by_exchange = total_investment_by_exchange
        
        summary.append({
            'Ticker': ticker,
            'Last Closing Price': last_close_price,
            'Balance Quantity': balance_quantity,
            'Average Buy Price': avg_buy_price,
            'Unrealized P/L': unrealized_pnl,
            'Realized P/L': realized_pnl,
            'Total Return': total_return,
            'Total Dividends': total_dividends,
            'Industry': industry , # Add industry information
            'Stock Exchange': stock_exchange
        })

    st.session_state.portfolio_summary = pd.DataFrame(summary)