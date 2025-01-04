import streamlit as st
import pandas as pd
from utils_backtest import fetch_financial_ratios, backtest_strategy, plot_backtest_results, strategy_params, fetch_dividends, plot_dividends, fetch_stock_data, plot_strategy, trading_strategy
import streamlit as st
from huggingface_hub import InferenceClient
from utils_markdown import display_md

# Insert at each page to interrupt the widget clean-up process
# https://docs.streamlit.io/develop/concepts/multipage-apps/widgets
if "tickers" in st.session_state:
    st.session_state.tickers = st.session_state.tickers

if "watchlist_name" in st.session_state:
    st.session_state.watchlist_name = st.session_state.watchlist_name

if "market" in st.session_state:
    st.session_state.market = st.session_state.market

col_trade, col_bot = st.columns([0.7, 0.3])

# --- Initialize the Inference Client with the API key ----#
client = InferenceClient(token=st.secrets.api_keys.huggingfacehub_api_token)

# set LLM model
model_option = {"qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
                "llama3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
                "llama3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                }

if "model_select" not in st.session_state:
    st.session_state.model_select = model_option.get("llama3.1-70b")

# persist tickers selection if user switch page
if "tickers" not in st.session_state:
    st.session_state.tickers = []

if "strategy" not in st.session_state:
    st.session_state.strategy = None 

# sidebar widgets
sidebar_widget = st.sidebar
# Streamlit app
model_select = sidebar_widget.selectbox(
    label="Pick a model to chat with Finley", options=model_option.keys(), index=2)

st.session_state.model_select = model_option.get(model_select)

exchange = sidebar_widget.selectbox(label= ":blue[**Stock Exchange**]",
                                    options=["SGX", "NYSE"])

# Load the CSV file containing stock symbols and names
# Create a dictionary for the dropdown menu
try:
    stocks_df = pd.read_csv(f"./resource/{exchange}.csv")
except FileNotFoundError:
    st.error(
        "The csv file was not found. Please ensure the file is in the same directory as the script.")
    stocks_df = pd.DataFrame(columns=['Symbol', 'Name'])

stock_options = dict(zip(stocks_df['Symbol'], stocks_df['Name']))


# store chat conversations with session state
if 'msg_history' not in st.session_state:

    st.session_state.msg_history = []

    system_message = """You are friendly chatbot,Finley, that analyse stock investment information and assist user
    in their investment decisions. Look back at the chat history to find information if needed. Minimize
    summarizing the financial information as user can see it from the dashboard. """

    st.session_state.msg_history.append(
        {"role": "system", "content": f"{system_message}"})

    st.session_state.msg_history.append(
        {"role": "assistant", "content": f"Pick a few stocks and a trading strategy at the sidebar. If you’re deciding to invest between Stock A and Stock B say for a 6–12 month time horizon, I can help you to make sense of their performance and provide recommendations to help you choose the better investment."})


with col_bot:
    st.write("###")
    st.write("**:blue[Chat with Finley]**")

    messages = st.container(border=True, key="messages_container")

    for msg in st.session_state.msg_history:
        if msg['role'] != "system":
            messages.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Ask a question..."):

        # Append the user's input to the msg_history
        st.session_state.msg_history.append(
            {"role": "user", "content": user_input})

        # write current chat on UI
        messages.chat_message("user").write(user_input)

        # ----- Create a placeholder for the streaming response ------- #
        with messages.empty():
            # Stream the response

            stream = client.chat_completion(
                model=st.session_state.model_select,
                messages=st.session_state.msg_history,
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
        st.session_state.msg_history.append(
            {"role": "assistant", "content": collected_response})

        # Keep history to 3, pop 2nd item from the list
        #if len(st.session_state.msg_history) >= 3:
        #    st.session_state.msg_history.pop(1)

    if st.button('Clear chat'):
        st.session_state.msg_history = st.session_state.msg_history[:2]
        messages.empty()
        st.rerun()
        #messages = st.container(border=True)


    disclaimer_text = """Disclaimer:
    The information and recommendations provided by Finley are for educational and informational purposes only and should not be considered as financial advice or a guarantee of future results. Investments in the stock market carry risks, including the potential loss of capital, and past performance does not guarantee future performance.
    Before making any investment decisions, you should conduct your own research, evaluate your financial situation, and consider consulting with a licensed financial advisor. Finley does not have access to all market data and cannot account for unforeseen events or changes in market conditions.
    By using this service, you acknowledge and accept that all investment decisions are made at your own discretion and risk."""

    display_md.display(disclaimer_text, color="#7d8796", font_size="10px", tag="p")


# User inputs


# Create a multiselect dropdown menu for stock selection
tickers = sidebar_widget.multiselect(label= ":blue[**Stock**]", 
                                    options=list(stock_options.keys()), 
                                    format_func=lambda x: f"{x} - {stock_options[x]}", 
                                    placeholder="Select one or more", 
                                    key='tickers',
                                    )

# persist selected tickers in session state to retain page memory
#st.session_state.tickers = tickers
#if tickers:
#    st.write(f'You selected: {tickers}')

if len(tickers):
    strategy = sidebar_widget.selectbox(label=":blue[Trading Strategy]", options=trading_strategy, index=0)
    
    st.session_state.strategy = strategy

    #if strategy != "":
    if strategy:
        # Create a selectbox for time period selection
        period = sidebar_widget.selectbox(":blue[Time Period]", [
            "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=4)

        # Get the parameters for the selected strategy
        # (strategy_params dict is located in utils.py)
        params = strategy_params.get(strategy, {})

        # Initialize variables to hold the parameter values
        sma_period = None
        ema_period = None
        bb_period = None
        bb_std = None
        macd_fast = None
        macd_slow = None
        macd_signal = None
        rsi_period = None

        # Create number inputs for each parameter based on the selected strategy and
        # update last key/value pair in strategy_params for session state msg history

        if "sma_period" in params:
            sma_period = sidebar_widget.number_input(
                ":blue[SMA Period (days)]", **params["sma_period"])
           
            strategy_params[strategy]["period_select"].update({"sma period (days)": sma_period})

        if "ema_period" in params:
            ema_period = sidebar_widget.number_input(
                ":blue[EMA Period (days)]", **params["ema_period"])
            strategy_params[strategy]["period_select"].update({"ema period (days)": ema_period})

        if "bb_period" in params:
            bb_period = sidebar_widget.number_input(
                ":blue[Bollinger Bands Period (days)]", **params["bb_period"])
            strategy_params[strategy]["period_select"].update({"Bollinger Bands Period (days)": bb_period})
        
        if "bb_std" in params:
            bb_std = sidebar_widget.number_input(
                ":blue[Bollinger Bands Standard Deviations]", **params["bb_std"])
            strategy_params[strategy]["period_select"].update({"Bollinger Bands Standard Deviations": bb_std})
                
        if "macd_fast" in params:
            macd_fast = sidebar_widget.number_input(
                ":blue[MACD Fast Period (days)]", **params["macd_fast"])
            strategy_params[strategy]["period_select"].update({"MACD Fast Period (days)": macd_fast})

        if "macd_slow" in params:
            macd_slow = sidebar_widget.number_input(
                ":blue[MACD Slow Period (days)]", **params["macd_slow"])
            strategy_params[strategy]["period_select"].update({"MACD Slow Period (days)": macd_slow})

        if "macd_signal" in params:
            macd_signal = sidebar_widget.number_input(
                ":blue[MACD Signal Period (days)]", **params["macd_signal"])
            strategy_params[strategy]["period_select"].update({"MACD Signal Period (days)": macd_signal})
        
        if "rsi_period" in params:
            rsi_period = sidebar_widget.number_input(
                ":blue[RSI Period (days)]", **params["rsi_period"])
            strategy_params[strategy].update({"period_select": {"RSI Period (days):" : rsi_period}})

    # Button to trigger the analysis
    #analyze_button = sidebar_widget.button(
    #    'Analyze', on_click=on_button_click)

    #if st.session_state.button_clicked:


        with col_trade:

            # with st.container(height=700):

            for ticker in st.session_state.tickers:

                # fetch stock data, backtest, financial ratios, dividends
                hist, strategy = fetch_stock_data(ticker, period, sma_period, ema_period, bb_period,
                                                  bb_std, macd_fast, macd_slow, macd_signal, rsi_period, strategy)
                hist, metrics = backtest_strategy(hist, strategy)
                ratios = fetch_financial_ratios(ticker)
                dividends_df = fetch_dividends(ticker)

                st.subheader(stock_options[ticker])

                tab_1, tab_2, tab_3 = st.tabs(
                    [":blue-background[Buy/Sell Signals]", ":blue-background[Backtest Returns]", ":blue-background[Dividend Returns]"])

                # backtest text in col1, financial ratios in col2
                col1, col2 = st.columns([0.6, 0.4], gap="large")

                with col1:
                    display_md.display(metrics)


                # write financial ratios as dataframe
                with col2:
                    #st.write(f":blue[**Financial Indicators**]")
                    st.dataframe(ratios, hide_index=True,
                                height=450, use_container_width=True)

                with tab_1:
                    # plot trade strategy (buy/sell signal)
                    plot_strategy(hist, ticker, strategy,
                                  bb_period, bb_std)

                with tab_2:
                    # plot backtest
                    plot_backtest_results(hist, ticker)

                with tab_3:
                    # plot dividends
                    plot_dividends(dividends_df, ticker)

                st.session_state.msg_history.append(
                    {"role": "system", "content": f"Here are the backtesting results {metrics} for {ticker} and the selected parameters: period = {period}, parameters = {strategy_params[strategy]['period_select']}"})
                st.session_state.msg_history.append(
                    {"role": "system", "content": f"Here are the financial ratios {ratios} for {ticker}"})
                st.session_state.msg_history.append(
                    {"role": "system", "content": f"Here are the dividends {dividends_df} for {ticker}"})
                

                #st.write(f"and the selected parameters: period = {period}, parameters = {strategy_params[strategy]['period_select']}")