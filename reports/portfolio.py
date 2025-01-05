import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date
from utils_portfolio import update_portfolio_summary
from pathlib import Path
from utils_gdrive import upload_to_google_drive, load_data
import plotly.express as px
import plotly.graph_objects as go
from utils_markdown import display_md


# Insert at each page to interrupt the widget clean-up process
# https://docs.streamlit.io/develop/concepts/multipage-apps/widgets

#if "tickers" in st.session_state:
#    st.session_state.tickers = st.session_state.tickers
#
#if "watchlist_name" in st.session_state:
#    st.session_state.watchlist_name = st.session_state.watchlist_name
#    
#if "market" in st.session_state:
#    st.session_state.market = st.session_state.market
    
# Set file path and initialize session state for buy and sell transactions 
buy_transaction_fp = Path(f'user_data/{st.session_state.user_id}/portfolio/buy_transactions.csv')
sell_transaction_fp = Path(f'user_data/{st.session_state.user_id}/portfolio/sell_transactions.csv')

if 'buy_transactions' not in st.session_state:
    # use existing transaction records if exists
    if buy_transaction_fp.exists():
        st.session_state.buy_transactions = pd.read_csv(buy_transaction_fp)
    # create an empty DF
    else:
        st.session_state.buy_transactions = pd.DataFrame(columns=['Ticker', 'Quantity', 'Buy Date', 'Buy Price', 'Stock Exchange'])

if 'sell_transactions' not in st.session_state:
    # use existing transaction records if exists
    if sell_transaction_fp.exists():
        st.session_state.sell_transactions = pd.read_csv(sell_transaction_fp)
    # create an empty DF
    else:
        st.session_state.sell_transactions = pd.DataFrame(columns=['Ticker', 'Quantity', 'Sell Date', 'Sell Price', 'Stock Exchange'])

# Load portfolio summary if exists
if not st.session_state.buy_transactions.empty: #and not st.session_state.sell_transactions.empty:
    update_portfolio_summary()
    
#  Initialize session state for portfolio
if 'portfolio_summary' not in st.session_state:
    st.session_state.portfolio_summary = pd.DataFrame(columns=['Ticker', 
                                                               'Last Closing Price',
                                                               'Balance Quantity', 
                                                               'Average Buy Price', 
                                                               'Unrealized P/L', 
                                                               'Realized P/L', 
                                                               'Total Return', 
                                                               'Total Dividends',
                                                               'Industry',
                                                               'Stock Exchange'])

if 'total_investment_by_exchange' not in st.session_state:
    st.session_state.total_investment_by_exchange = pd.DataFrame(columns=['Stock Exchange', 'Total Investment'])

# set filepath for writing buy and sell transactions entry at sidebar
portfolio_folder = Path(f'user_data/{st.session_state.user_id}/portfolio')

# Streamlit app
#st.title("Stock Investment Portfolio")
#display_md.display("Stock Investment Portfolio",  font_size="28px", color='#1c51ba')
st.write("##### :blue[Portfolio Dashboard]")

with st.sidebar:

    # User selects a stock exchange 
    market = st.selectbox(
        label=":blue[**Stock Exchange**]", options=["SGX", "NYSE"])

    if market:
        # file path to SGX or NYSE company and symbols
        file_path = Path(f'resource/{market}.csv')  

        # Load the exchange data
        stock_data = load_data(file_path)

        # Create a dictionary to map names to symbols of stock data
        name_to_symbol = dict(zip(stock_data['Name'], stock_data['Symbol']))

    buy_tab1, sell_tab1, buy_tab2, sell_tab2 = st.tabs([":red-background[Buy]",":red-background[Sell]", "Edit Buy",  "Edit Sell"])

    # Add Buy Transaction tab
    with buy_tab1:
        with st.form("buy_form"):
            selected_name = st.selectbox(
                'Select Stocks',
                options=stock_data['Name'],
                index=None
            )
            buy_ticker = name_to_symbol.get(selected_name)

            buy_date = st.date_input("Buy Date")
            buy_quantity = st.number_input("Buy Quantity", min_value=1, step=1)
            buy_price = st.number_input("Buy Price", min_value=0.01, step=0.01)
            buy_submit = st.form_submit_button("Add")

        if buy_submit:
            new_buy = pd.DataFrame({
                'Ticker': [buy_ticker],
                'Quantity': [buy_quantity],
                'Buy Date': [buy_date],
                'Buy Price': [buy_price],
                'Stock Exchange': [market]  # Add stock exchange information
            })
            st.session_state.buy_transactions = pd.concat([st.session_state.buy_transactions, new_buy], ignore_index=True)

            st.session_state.buy_transactions.to_csv(portfolio_folder / "buy_transactions.csv", index=False)
            update_portfolio_summary()
            upload_to_google_drive()

    # Update Buy Transaction tab
    with buy_tab2:
        with st.form("update_buy_form"):
            if not st.session_state.buy_transactions.empty:
                buy_update_ticker = st.selectbox("Ticker Symbol", 
                                                            st.session_state.buy_transactions['Ticker'].unique())
                updated_buy_date = st.date_input("Buy Date")
                updated_buy_quantity = st.number_input("Buy Quantity", min_value=1, step=1)
                updated_buy_price = st.number_input("Buy Price", min_value=0.01, step=0.01)
                update_buy_submit = st.form_submit_button("Update")

                if update_buy_submit:
                    st.session_state.buy_transactions.loc[
                        st.session_state.buy_transactions['Ticker'] == buy_update_ticker, 
                        ['Quantity', 'Buy Date', 'Buy Price']
                    ] = updated_buy_quantity, updated_buy_date, updated_buy_price
                    st.session_state.buy_transactions.to_csv(portfolio_folder / "buy_transactions.csv", index=False)
                    update_portfolio_summary()
                    upload_to_google_drive()
            else:
                st.write("No buy transactions available to update.")

    # Add Sell Transaction tab
    with sell_tab1:
        with st.form("sell_form"):
            sell_ticker = st.selectbox("Ticker Symbol", st.session_state.buy_transactions['Ticker'].unique())
            sell_date = st.date_input("Sell Date")
            sell_quantity = st.number_input("Sell Quantity", min_value=1, step=1)
            sell_price = st.number_input("Sell Price", min_value=0.01, step=0.01)
            sell_submit = st.form_submit_button("Sell")

        if sell_submit:
            new_sell = pd.DataFrame({
                'Ticker': [sell_ticker],
                'Quantity': [-sell_quantity],  # Convert sell quantity to negative
                'Sell Date': [sell_date],
                'Sell Price': [sell_price],
                'Stock Exchange': [market]  # Add stock exchange information
            })
            st.session_state.sell_transactions = pd.concat([st.session_state.sell_transactions, new_sell], ignore_index=True)
            st.session_state.sell_transactions.to_csv(portfolio_folder / "sell_transactions.csv",index=False)
            update_portfolio_summary()
            upload_to_google_drive()

    # Update Sell Transaction tab
    with sell_tab2:
        with st.form("update_sell_form"):
            if not st.session_state.sell_transactions.empty:
                sell_update_ticker = st.selectbox("Ticker Symbol",
                                                                st.session_state.sell_transactions['Ticker'].unique())
                updated_sell_date = st.date_input("Sell Date")
                updated_sell_quantity = st.number_input("Sell Quantity", min_value=1, step=1)
                updated_sell_price = st.number_input("Sell Price", min_value=0.01, step=0.01)
                update_sell_submit = st.form_submit_button("Update")

                if update_sell_submit:

                    st.session_state.sell_transactions.loc[
                        st.session_state.sell_transactions['Ticker'] == sell_update_ticker,
                        ['Quantity', 'Sell Date', 'Sell Price']
                    ] = updated_sell_quantity, updated_sell_date, updated_sell_price
                    st.session_state.sell_transactions.to_csv(portfolio_folder / "sell_transactions.csv",index=False)
                    update_portfolio_summary()
                    upload_to_google_drive()
            else:
                st.write("No sell transactions available to update.")

# Portfolio Summary, Buy Transactions, and Sell Transactions in tabs
tab1, tab2, tab3 = st.tabs([f":red-background[Portfolio Summary]",
                            f":red-background[Buy Transactions]",
                            f":red-background[Sell Transactions]"])

# Portfolio Summary tab
with tab1:
    if not st.session_state.portfolio_summary.empty:
        def color_negative_red_positive_blue(val):
            """
            Colors elements in a DataFrame red if negative, blue if positive.
            """
            color = '#04b568' if val >= 0 else '#f5651d'
            return f'color: {color}'

        styled_summary = st.session_state.portfolio_summary.style.format({
            'Last Closing Price': "{:.2f}", 
            'Average Buy Price': "{:.2f}",
            'Unrealized P/L': "{:.2f}",
            'Realized P/L': "{:.2f}",
            'Total Return': "{:.2f}%",
            'Total Dividends': "{:.2f}"
        }).applymap(color_negative_red_positive_blue, subset=['Unrealized P/L', 'Realized P/L', 'Total Return'])

        st.dataframe(
            styled_summary,
            use_container_width=True,
            hide_index=True
        )




        #display_md.display("Visualization", font_size="28px", color='#1c51ba')
        st.write("##### :blue[Portfolio Visualization]")
        p1, p2, p3, p4, p5, p6 = st.tabs(['Profit & Loss', 
                                      'Total Return', 
                                      'Total Dividends', 
                                      'Industry Distribution', 
                                      'Correlation',
                                      'Total Investment'])
        
        with p6:
            # Display total investment by stock exchange
            #st.write("###### :grey[Investment by Stock Exchange]")
            st.dataframe(
                st.session_state.total_investment_by_exchange.style.format({
                    'Total Investment': "{:.2f}"
                }),
                use_container_width=False,
                hide_index=True
            )


        with p1:
            # Bar Chart for Unrealized P/L and Realized P/L
            fig1 = px.bar(st.session_state.portfolio_summary, x='Ticker', y=['Unrealized P/L', 'Realized P/L'],
                        #title='Unrealized vs Realized Profit and Loss',
                        barmode='group',
                        color_discrete_map={'Unrealized P/L': '#4c8a5c', 'Realized P/L': '#25748f'})
            
            # Update the layout to center the title
            fig1.update_layout(
                title={
                    'text': 'Unrealized vs Realized Profit and Loss',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {
                        'color': '#565a61',  # Set the font color to red
                        'family': 'Arial, sans-serif',  # Set the font family to Arial
                        'size': 14,  # Set the font size to 24
                    }
                }
            )
            st.plotly_chart(fig1)

        with p2:
            # Pie Chart for Total Return
            fig2 = px.pie(st.session_state.portfolio_summary, 
                          names='Ticker', 
                          values='Total Return',
                          hole=0.4,
                          title='Distribution of Total Return')
            
                    # Update the layout to center the title
            fig2.update_layout(
                title={
                    'text': 'Distribution of Total Return',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {
                        'color': '#565a61',  # Set the font color to red
                        'family': 'Arial, sans-serif',  # Set the font family to Arial
                        'size': 14,  # Set the font size to 24
                    }
                }
            )
            
            st.plotly_chart(fig2)

        with p3:
            # Bar Chart for Total Dividends
            fig3 = px.bar(st.session_state.portfolio_summary, x='Ticker', y='Total Dividends',
                        title='Total Dividends by Ticker')
            fig3.update_layout(
                title={
                    'text': 'Total Dividends by Ticker',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {
                        'color': '#565a61',  # Set the font color to red
                        'family': 'Arial, sans-serif',  # Set the font family to Arial
                        'size': 14,  # Set the font size to 24
                    }
                }
            )
            st.plotly_chart(fig3)

        with p4:
            # Stacked Bar Chart for Industry Distribution
            industry_counts = st.session_state.portfolio_summary['Industry'].value_counts()
            fig4 = px.bar(industry_counts, 
                        title='Industry Distribution of Portfolio',
                        labels={'index': 'Industry', 'value': 'Number of Stocks'},
                        color_discrete_sequence=['#4c8a5c'])
            fig4.update_layout(
                title={
                    'text': 'Industry Distribution of Portfolio',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {
                        'color': '#565a61',  # Set the font color to red
                        'family': 'Arial, sans-serif',  # Set the font family to Arial
                        'size': 14,  # Set the font size to 24
                    }
                }
            )
            
            st.plotly_chart(fig4)

        with p5:
            # Heatmap for Correlation
            tickers =  st.session_state.portfolio_summary['Ticker'].tolist()
            data = yf.download(tickers, period="1y")['Close']
            correlation_matrix = data.corr()
            fig5 = px.imshow(correlation_matrix, 
                            labels=dict(x="Ticker", y="Ticker", color="Correlation"), 
                            x=tickers, 
                            y=tickers, 
                            title='Correlation Heatmap of Portfolio Stocks',
                            zmin=-1,  # Set the minimum value to -1
                            zmax=1,   # Set the maximum value to 1
                            color_continuous_scale='RdBu_r')  # Use a diverging color scale
            fig5.update_layout(
                title={
                    'text': 'Correlation Heatmap',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {
                        'color': '#565a61',  # Set the font color to red
                        'family': 'Arial, sans-serif',  # Set the font family to Arial
                        'size': 14,  # Set the font size to 24
                    }
                }
            )
            

            st.plotly_chart(fig5)
    else:
        st.write("No portfolio data available.")

# Buy Transactions tab
with tab2:
    if not st.session_state.buy_transactions.empty:
        st.dataframe(
            st.session_state.buy_transactions.style.format({
                'Buy Price': "{:.2f}"
            }),
            use_container_width=True
        )
        st.download_button(
            "Download CSV",
            st.session_state.buy_transactions.to_csv(index=False),
            "buy_transactions.csv",
            "text/csv",
        )
    else:
        st.write("No buy transactions available.")

# Sell Transactions tab
with tab3:
    if not st.session_state.sell_transactions.empty:
        st.dataframe(
            st.session_state.sell_transactions.style.format({
                'Sell Price': "{:.2f}"
            }),
            use_container_width=True
        )
        st.download_button(
            "Download CSV",
            st.session_state.sell_transactions.to_csv(index=False),
            "sell_transactions.csv",
            "text/csv",
        )
    else:
        st.write("No sell transactions available.")
