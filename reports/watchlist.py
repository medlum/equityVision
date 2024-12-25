import streamlit as st
import pandas as pd
import yfinance as yf
import json
from pathlib import Path
import matplotlib.pyplot as plt
from utils_watchlist import *
from utils_markdown import display_md

# Ensure the watchlist folder exists
watchlist_folder = Path(f'user_data/{st.session_state.user_id}/watchlist')
watchlist_folder.mkdir(parents=True, exist_ok=True)

# Select market
market = st.sidebar.selectbox(
    label=":blue[**Stock Exchange**]", options=["SGX", "NYSE"])

# Determine the file path based on the selected market
file_path = Path(f'resource/{market}.csv')
watchlist_file_path = watchlist_folder / f'watchlist_{market}.json'

# Load the stock data
stock_data = load_data(file_path)

# Load the existing watchlists
watchlists = load_watchlists(watchlist_file_path)

# Sidebar UI for managing watchlists
#st.sidebar.subheader(":blue[Watchlists]")

# Dropdown to select existing watchlist or create new one
if watchlists:

    existing_watchlists = list(watchlists.keys())

    watchlist_action = st.sidebar.radio(
        ":blue[**Watchlist Action**]",
        horizontal=True,
        options=["Use Existing", "Create New"]
    )

    if watchlist_action == "Use Existing":
        watchlist_name = st.sidebar.selectbox(
            "Select Watchlist", options=existing_watchlists, index=None)
    else:
        watchlist_name = st.sidebar.text_input(
            "Enter a new watchlist name", "New Watchlist")
else:
    watchlist_action = "Create New Watchlist"  # Define watchlist_action here
    st.sidebar.warning("No watchlists available. Please create a new one.")

    watchlist_name = st.sidebar.text_input(
            "Enter a new watchlist name", "New Watchlist", disabled=True)

# Load the selected symbols from the watchlist
selected_symbols = watchlists.get(watchlist_name, [])

# Create a dictionary to map names to symbols
name_to_symbol = dict(zip(stock_data['Name'], stock_data['Symbol']))

# Multi-select widget for selecting stocks
selected_names = st.sidebar.multiselect(
    'Select Stocks',
    options=stock_data['Name'],
    #default=None
    default=[name for name, symbol in name_to_symbol.items()
             if symbol in selected_symbols]
)

# Map selected names back to symbols
selected_symbols = [name_to_symbol[name] for name in selected_names]

# Enable or disable the "Save Watchlist" button based on conditions
#if (watchlist_action == "Use Existing Watchlist" and selected_names) or (watchlist_action == "Create New Watchlist" and selected_names):
#    save_button_disabled = False
#else:
#    save_button_disabled = True

# Save the watchlist
if st.sidebar.button("Save Watchlist"):
    if watchlist_name:
        watchlists[watchlist_name] = selected_symbols
        save_watchlists(watchlist_file_path, watchlists)
        st.sidebar.success(f"Watchlist '{watchlist_name}' saved successfully!")
        upload_to_google_drive()
        st.sidebar.success(
            f"Watchlist '{watchlist_name}' uploaded to Google Drive!")
    else:
        st.sidebar.error("Please enter a valid name for the watchlist.")


# Fetch and display the stock data for the selected symbols
if selected_symbols:

    st.write(f"#### :blue[{watchlist_name}]")
    fetch_and_display_price(selected_symbols)

    tab_names = [f":blue-background[{name}]" for name in selected_names]

    tabs = st.tabs(tab_names)
    # st.selectbox("symbol", options=selected_names)

    # Display analyst recommendations
    for tab, symbol in zip(tabs, selected_symbols):
        with tab:
            _stock = yf.Ticker(symbol)
            # stock.history(period="2y")

            with st.container():

                col3, col4 = st.columns(
                    2, gap="large", vertical_alignment="top")

                with col3:
                    plot_stock_data(symbol=symbol, period='1y')

                with col4:
                    # fetch dividends
                    filtered_data = fetch_dividends(_stock)
                    plot_dividends(filtered_data)

                # with col5:
                # fetch analysts recommendations
                data, numeric_df, max_value = fetch_recommendations(
                    _stock)
                if data is not None:
                    plot_recommendations(data, numeric_df, max_value)
                else:
                    st.warning("Recommendation plot is not available")

            with st.container(height=400):
                col1, col2 = st.columns(
                    2, gap="large", vertical_alignment="top")
                with col1:
                    # fetch earnings calendar
                    display_md.display("Earnings Calendar")
                    earnings_calendar = fetch_earnings_calendar(_stock)
                    if not earnings_calendar:
                        st.warning("Not Available")
                    else:
                        st.dataframe(earnings_calendar, hide_index=True)
                    

                with col2:
                    # fetch upgrades
                    display_md.display("Securities Firm Call")
                    upgrades_downgrades = fetch_upgrades_downgrades(_stock)
                    if upgrades_downgrades.empty:
                        st.warning("Not Available")
                    else:
                        st.write(upgrades_downgrades)

    # else:
    #    st.error("No data available for the selected stocks.")
else:
    st.write(f"#### :red[{watchlist_name}]")
    st.write("No stocks selected.")
