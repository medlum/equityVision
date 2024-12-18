import streamlit as st
import pandas as pd
from utils_trade import fetch_financial_ratios, backtest_strategy, plot_backtest_results, strategy_params, fetch_dividends, plot_dividends, fetch_stock_data, plot_strategy, markdown_disclaimer
import streamlit as st
from huggingface_hub import InferenceClient


col_trade, col_bot = st.columns([0.7, 0.3])

# --- Initialize the Inference Client with the API key ----#
client = InferenceClient(token=st.secrets["huggingfacehub_api_token"])

# set LLM model
model_option = {"qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
                "qwen2.5-coder": "Qwen/Qwen2.5-Coder-32B-Instruct",
                "llama3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
                "llama3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "llama3-8b": "meta-llama/Meta-Llama-3-8B-Instruct",
                }

if "model_select" not in st.session_state:
    st.session_state.model_select = model_option.get("llama3.1-70b")

# Initialize session state variable if it doesn't exist
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False


def on_button_click():
    # Define a function to handle button click
    st.session_state.button_clicked = not st.session_state.button_clicked


# sidebar widgets
sidebar_widget = st.sidebar
# Streamlit app
model_select = sidebar_widget.selectbox(
    label="Pick a model to chat with Finley", options=model_option.keys(), index=3)

st.session_state.model_select = model_option.get(model_select)
exchange = sidebar_widget.selectbox(label="Choose Stock Exchange",
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
        {"role": "assistant", "content": f"To get started, pick a few stocks and a trading strategy at the sidebar. For example, if you’re deciding between Stock A and Stock B for a 6–12 month time horizon, I can analyze their performance and provide recommendations to help you choose the better investment."})


with col_bot:
    st.write("###")
    st.write("**:blue[Chat with Finley]**")

    messages = st.container(border=True)

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
        if len(st.session_state.msg_history) >= 3:
            st.session_state.msg_history.pop(1)

    markdown_disclaimer()


# User inputs
# Create a multiselect dropdown menu for stock selection
tickers = sidebar_widget.multiselect("Choose Stock for Backtest", list(
    stock_options.keys()), format_func=lambda x: f"{x} - {stock_options[x]}", placeholder="Accepts more than one counter",)


if len(tickers):
    strategy = sidebar_widget.selectbox(label="Choose Trading Strategy", options=[
        "Moving Average Crossover", "Bollinger Bands", "MACD", "RSI", ""], index=4)

    if strategy != "":
        # Create a selectbox for time period selection
        period = sidebar_widget.selectbox("Select Time Period:", [
            "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], index=5)

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

        # Create number inputs for each parameter based on the selected strategy
        if "sma_period" in params:
            sma_period = sidebar_widget.number_input(
                "Enter SMA Period (days):", **params["sma_period"])
        if "ema_period" in params:
            ema_period = sidebar_widget.number_input(
                "Enter EMA Period (days):", **params["ema_period"])
        if "bb_period" in params:
            bb_period = sidebar_widget.number_input(
                "Enter Bollinger Bands Period (days):", **params["bb_period"])
        if "bb_std" in params:
            bb_std = sidebar_widget.number_input(
                "Enter Bollinger Bands Standard Deviations:", **params["bb_std"])
        if "macd_fast" in params:
            macd_fast = sidebar_widget.number_input(
                "Enter MACD Fast Period (days):", **params["macd_fast"])
        if "macd_slow" in params:
            macd_slow = sidebar_widget.number_input(
                "Enter MACD Slow Period (days):", **params["macd_slow"])
        if "macd_signal" in params:
            macd_signal = sidebar_widget.number_input(
                "Enter MACD Signal Period (days):", **params["macd_signal"])
        if "rsi_period" in params:
            rsi_period = sidebar_widget.number_input(
                "Enter RSI Period (days):", **params["rsi_period"])

    # Button to trigger the analysis
    analyze_button = sidebar_widget.button(
        'Analyze', on_click=on_button_click)

    if st.session_state.button_clicked:

        with col_trade:

            # with st.container(height=700):

            for ticker in tickers:

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

                # generate backtest response
                col1.markdown(f"""
                                            <div style="text-align: justify">
                                                {metrics}
                                            </div>
                                            """,
                              unsafe_allow_html=True)

                # write financial ratios as dataframe
                col2.write(f":blue[**Financial Indicators**]")
                col2.dataframe(ratios, hide_index=True,
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
                    {"role": "system", "content": f"Here are the backtesting results {metrics} for {ticker}"})
                st.session_state.msg_history.append(
                    {"role": "system", "content": f"Here are the financial ratios {ratios} for {ticker}"})
                st.session_state.msg_history.append(
                    {"role": "system", "content": f"Here are the dividends {dividends_df} for {ticker}"})
