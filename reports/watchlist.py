import streamlit as st
import pandas as pd
import yfinance as yf
import json
from pathlib import Path
import matplotlib.pyplot as plt
from utils_watchlist import *
from utils_markdown import display_md, disclaimer_text
from utils_gdrive import upload_to_google_drive, load_data
from utils_llm import client, model_option

# initialize watchlist conversations 
if 'watchlist_history' not in st.session_state:

    st.session_state.watchlist_history = []

    system_message = """You are friendly chatbot,Finley, that analyse stock investment information and assist user
    in their investment decisions. Look back at the chat history to find information if needed. Minimize
    summarizing the financial information as user can see it from the dashboard. """

    st.session_state.watchlist_history.append(
        {"role": "system", "content": f"{system_message}"})

    st.session_state.watchlist_history.append(
        {"role": "assistant", "content": f"I can help you to make sense of your stock watchlist performance and provide recommendations to help you choose the better investment."})
    
if "watchlist_model_select" not in st.session_state:
    st.session_state.model_select = model_option.get("llama3.1-70b")


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
#
#if "watchlist_action" in st.session_state:
#    st.session_state.watchlist_action = st.session_state.watchlist_action

# initialize for text_input widget to remain stateful across pages

if "watchlist_name" not in st.session_state:
    st.session_state.watchlist_name = None
    
if "market" not in st.session_state:
    st.session_state.market = 'SGX'

if "watchlist_action" not in st.session_state:
    st.session_state.watchlist_action = "Use Existing"

# f'user_data/{st.session_state.user_id}/watchlist' is created at utils_entry_pt
# Ensure the user's watchlist folder exists
watchlist_folder = Path(f'user_data/{st.session_state.user_id}/watchlist')
watchlist_folder.mkdir(parents=True, exist_ok=True)

model_select = st.sidebar.selectbox(
    label="Pick a model to chat with Finley", options=model_option.keys(), index=2)


# User selects a stock exchange 
market = st.sidebar.selectbox(
    label=":blue[**Stock Exchange**]", 
    options=["SGX", "NYSE"],
    #key='market',
    )

if market:
    # file path to SGX or NYXSE company and symbols
    file_path = Path(f'resource/{market}.csv')

    # filepath to user's selected companies in watch list
    # for load_watchlist() and save_watchlists()
    watchlist_file_path = watchlist_folder / f'watchlist_{market}.json'

    # Load the exchange data
    stock_data = load_data(file_path)

    # Load the existing watchlist 
    # -> watchlist returns dict {}
    watchlists = load_watchlists(watchlist_file_path)

# Dropdown to select existing watchlist or create new one

# if watchlist is not empty
if watchlists:
    
    # get the values  of watchlist keys for selectbox
    existing_watchlists = list(watchlists.keys())

    watchlist_action = st.sidebar.radio(
        ":blue[**Watchlist Action**]",
        horizontal=True,
        options=["Use Existing", "Create New"],
        index=0,
        #key='watchlist_action'
    )

    # if use existing, display stock in the watchlist 
    if watchlist_action == "Use Existing":

        watchlist_name = st.sidebar.selectbox(
            "Select Watchlist", 
            options=existing_watchlists, 
            index=0,
            #key='watchlist_name'
           )

    # if create new, allow user to enter text
    else:
        watchlist_name = st.sidebar.text_input(
            "Enter a new watchlist name", "New Watchlist")

# if watchlist is empty, allow user to enter new list
else:
    # 
    watchlist_action = "Create New"  
    st.sidebar.warning("No watchlists available. Please create a new one.")

    watchlist_name = st.sidebar.text_input(
            "Enter a new watchlist name", "New Watchlist", disabled=False)

# Load the selected symbols from the watchlist
selected_symbols = watchlists.get(watchlist_name, [])

# Create a dictionary to map names to symbols of stock data
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

# Save the watchlist
if st.sidebar.button("Save Watchlist"):

    if watchlist_name:
        # put the created watchlist as the key to watchlists {}
        # and the symbols as the value 
        watchlists[watchlist_name] = selected_symbols
        # save watchlist to the file path
        save_watchlists(watchlist_file_path, watchlists)
        st.sidebar.success(f"Watchlist '{watchlist_name}' saved successfully!")
        # upload to google drive
        upload_to_google_drive()
        st.sidebar.success(
            f"Watchlist '{watchlist_name}' uploaded to Google Drive!")
    else:
        st.sidebar.error("Please enter a valid name for the watchlist.")

col_watchlist, col_bot = st.columns([0.7, 0.3], gap='medium')

with col_watchlist:
    # Fetch and display the stock data for the selected symbols
    if selected_symbols:

        st.write(f"#### :blue[{watchlist_name}]")
        fetch_and_display_price(selected_symbols)
        tab_names = [f":blue-background[{name}]" for name in selected_names]
        tabs = st.tabs(tab_names)

        for tab, symbol in zip(tabs, selected_symbols):
            with tab:
                _stock = yf.Ticker(symbol)

                #with st.container():
                
                st.write("###### Stock Price Chart")
                period = st.radio(label=":blue[*Select stock price interval*]",
                          options=['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
                           key=symbol,
                           horizontal=True,
                           index=4)
                plot_stock_data(symbol=symbol, period=period)

                # fetch dividends
                st.write("###### Dividends Trends")
                filtered_data = fetch_dividends(_stock)
                plot_dividends(filtered_data)

                # fetch analysts recommendations
                st.write("###### Analysts Recommendations")
                data, numeric_df, max_value = fetch_recommendations(_stock)
                if data is not None:
                    plot_recommendations(data, numeric_df, max_value)
                else:
                    st.warning("Recommendation plot is not available")

                #col1, col2 = st.columns([1,1], 
                #                              gap="small", 
                #                              vertical_alignment="top")
                
                tab_1, tab_2, tab_3 = st.tabs([f":red-background[Dividend Yield]", 
                                               f":red-background[Dividend Payout]", 
                                               f":red-background[Valuation]"])
                with tab_1:
                    #st.write("##### Dividend Yield ")
                    dividends_and_splits_data = get_dividends_and_splits(_stock)
                    st.dataframe(dividends_and_splits_data, hide_index=True)
                    
                with tab_2:
                    #st.write("##### Dividend Payout")
                    dividend_payout = get_dividend_details(_stock)
                    st.dataframe(dividend_payout, hide_index=True)

                with tab_3:
                    #st.write("##### Valuation")
                    valuation_data = get_valuation_measures(_stock)
                    st.dataframe(valuation_data,width=300, hide_index=True)

                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the valuation metrics for {_stock}: {valuation_data}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the dividends payout data for {_stock}: {dividend_payout}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the dividends splits data for {_stock}: {dividends_and_splits_data}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the analysts recommendations for {_stock}: {data}"})
                
    else:
        st.write(f"#### :red[{watchlist_name}]")
        st.write("No stocks selected.")





with col_bot:
    st.write("###")
    st.write("**:blue[Chat with Finley]**")

    messages = st.container(border=True, key="messages_container")

    for msg in st.session_state.watchlist_history:
        if msg['role'] != "system":
            messages.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Ask a question..."):

        # Append the user's input to the watchlist_history
        st.session_state.watchlist_history.append(
            {"role": "user", "content": user_input})

        # write current chat on UI
        messages.chat_message("user").write(user_input)

        # ----- Create a placeholder for the streaming response ------- #
        with messages.empty():
            # Stream the response

            stream = client.chat_completion(
                model=st.session_state.model_select,
                messages=st.session_state.watchlist_history,
                temperature=0.6,
                max_tokens=4524,
                top_p=0.7,
                stream=True,)

            # Initialize an empty string to collect the streamed content
            collected_response = ""

            # Stream the response and update the placeholder in real-time
            for chunk in stream:
                if 'delta' in chunk.choices[0] and 'content' in chunk.choices[0].delta:
                    collected_response += chunk.choices[0].delta.content
                    st.chat_message("assistant").write(
                        collected_response)

        # Add the assistant's response to the conversation history
        st.session_state.watchlist_history.append(
            {"role": "assistant", "content": collected_response})

    if st.button('Clear chat'):
        st.session_state.watchlist_history = st.session_state.watchlist_history[:2]
        messages.empty()
        st.rerun()
        #messages = st.container(border=True)

    display_md.display(disclaimer_text, color="#7d8796", font_size="10px", tag="p")





            # fetch earnings calendar
            #    display_md.display("Earnings Calendar")
            #    earnings_calendar = fetch_earnings_calendar(_stock)
            #    if not earnings_calendar:
            #        st.warning("Not Available")
            #    else:
            #        st.dataframe(earnings_calendar, hide_index=True)
            #    


            
            # fetch upgrades
            #if market == "NYSE":
            #    display_md.display("Securities Firm Call")
            #    upgrades_downgrades = fetch_upgrades_downgrades(_stock)
            #if upgrades_downgrades.empty:
            #    st.warning("Not Available")
            #else:
            #    st.write(upgrades_downgrades)