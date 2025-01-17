import streamlit as st
import pandas as pd
import yfinance as yf
import json
from pathlib import Path
import matplotlib.pyplot as plt
from utils_watchlist import *
from utils_markdown import display_md, disclaimer_text, quote_text
from utils_gdrive import upload_to_google_drive, load_data
from utils_llm import client, model_option
from utils_banner import breakingnews, news


breakingnews(news, '', 'filled')  
#---- initialize watchlist conversations ---#
if 'watchlist_history' not in st.session_state:

    st.session_state.watchlist_history = []

    system_message = """You are friendly chatbot,Finley, that analyse stocks information to assist the user
    in his or her investment decisions. Use the valuation, dividends, analyst recommendations and financial highlights to evaluate the  
    which stocks are better for investments."""

    st.session_state.watchlist_history.append(
        {"role": "system", "content": f"{system_message}"})

    st.session_state.watchlist_history.append(
        {"role": "assistant", "content": f"I can help you to make sense of your stock watchlist performance and provide recommendations to help you choose the better investment."})
    

model_select = st.sidebar.selectbox(
    label="**:blue[Pick a model to chat with Finley]**", options=model_option.keys(), index=1)


#--- initalize session state ---#

# set 0 as value for index param in exchange selectbox
if "selected_exchange" not in st.session_state:
    st.session_state.selected_exchange = 0

# to store key as  SGX or NYSE and value as integer to index watchlist
if "selected_watchlist" not in st.session_state:
    st.session_state.selected_watchlist = {}


#--- set filepath to user's watchlist ---#
# f'user_data/{st.session_state.user_id}/watchlist' is created at utils_entry_pt
# Ensure the user's watchlist folder exists
watchlist_folder = Path(f'user_data/{st.session_state.user_id}/watchlist')
watchlist_folder.mkdir(parents=True, exist_ok=True)

# store session state as variable for index param in exchange selectbox
current_exchange = st.session_state.selected_exchange
exchange_option = ["SGX", "NYSE"]

# User selects a stock exchange
exchange = st.sidebar.selectbox(
    label=":blue[**Stock Exchange**]", 
    options=exchange_option, 
    index=current_exchange, # refer to st.session_state.selected_exchange
    on_change=clear_history
    )

if exchange:
    # return index of selected exchange and assign to index param of exchange selectbox
    # this to maintain exchange state
    st.session_state.selected_exchange = exchange_option.index(exchange)
    
    # file path to SGX or NYXSE company and symbols
    file_path = Path(f'resource/{exchange}.csv')

    # filepath to user's selected companies in watch list
    # for load_watchlist() and save_watchlists()
    watchlist_file_path = watchlist_folder / f'watchlist_{exchange}.json'

    # Load the exchange data
    stock_data = load_data(file_path)

    # Load the existing watchlist 
    # -> watchlist returns dict {}
    watchlists = load_watchlists(watchlist_file_path)

    #  store session state as variable for index param in watchlist_name selectbox 
    # to retain state, current_watchlist is integer
    current_watchlist = st.session_state.selected_watchlist.get(exchange, 0)

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
        on_change=clear_history
    )

    # if use existing, display stock in the watchlist 
    if watchlist_action == "Use Existing":
        #watchlist_name = st.sidebar.selectbox(
        #    "Select Watchlist", 
        #    options=existing_watchlists, 
        #    index=current_watchlist,  #store as session state to retain selection
        #    on_change=clear_history        
        #   )
        
        # watchlist_name is integer at this part of the code
        watchlist_name = st.sidebar.pills(
            "Select Watchlist",
            options=existing_watchlists,
            default=existing_watchlists[current_watchlist] if current_watchlist < len(existing_watchlists) else 0,
            on_change=clear_history
        )


        # Update session state with the selected_watchlist based on the selected exchange
        st.session_state.selected_watchlist[exchange] = existing_watchlists.index(watchlist_name) # since watchlist_name is an integer, we can use index() to find the name of the existing watch_list

    # if create new, allow user to enter text
    elif watchlist_action == "Create New":
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
    '**:blue[Select Stocks]**',
    options=stock_data['Name'],
    #default=None
    default=[name for name, symbol in name_to_symbol.items()
             if symbol in selected_symbols]
)

# Map selected names back to symbols
selected_symbols = [name_to_symbol[name] for name in selected_names]

# Save the watchlist
if st.sidebar.button("Save Watchlist", type='primary', icon=":material/bookmark_add:"):
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
        
        #display_md.display(quote_text, color="#434a45", font_size="10px", tag='p')
        st.write(f"#### :grey[{watchlist_name}]")
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
                analyst_rec, numeric_df, max_value = fetch_recommendations(_stock)
                if analyst_rec is not None:
                    plot_recommendations(analyst_rec, numeric_df, max_value)
                else:
                    st.warning("Recommendation plot is not available")

                
                tab_1, tab_2, tab_3, tab_4 = st.tabs([f":red-background[Dividend Yield]", 
                                               f":red-background[Dividend Payout]", 
                                               f":red-background[Financial Valuation]",
                                               f":red-background[Financial Highlights]"])
                with tab_1:
                    #st.write("##### Dividend Yield ")
                    dividends_and_splits_data = get_dividends_and_splits(_stock)
                    st.dataframe(dividends_and_splits_data, hide_index=True, width=400)
                    
                with tab_2:
                    #st.write("##### Dividend Payout")
                    dividend_payout = get_dividend_details(_stock)
                    st.dataframe(dividend_payout, hide_index=True)

                with tab_3:
                    #st.write("##### Valuation")
                    valuation_data = get_valuation_measures(_stock)
                    st.dataframe(valuation_data,width=300, hide_index=True)

                with tab_4:
                    financial_highlights = get_financial_highlights(_stock)
                    st.dataframe(financial_highlights, width = 300, height=460,hide_index=True)
                    

                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the valuation metrics for {_stock}: {valuation_data}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the dividends payout data for {_stock}: {dividend_payout}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the dividends splits data for {_stock}: {dividends_and_splits_data}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the analysts recommendations for {_stock}: {analyst_rec}"})
                st.session_state.watchlist_history.append(
                    {"role": "system", "content": f"Here are the financial highlights for {_stock}: {financial_highlights}"})

                
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
                model=model_option[model_select],
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

    if st.button('Clear',type='primary', icon=":material/delete_forever:"):
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
            #if exchange == "NYSE":
            #    display_md.display("Securities Firm Call")
            #    upgrades_downgrades = fetch_upgrades_downgrades(_stock)
            #if upgrades_downgrades.empty:
            #    st.warning("Not Available")
            #else:
            #    st.write(upgrades_downgrades)