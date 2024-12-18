
import pathlib
import json
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import time


# Function to load watchlists from a JSON file


def load_watchlists(file_path):
    if file_path.exists():
        with file_path.open('r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
            else:
                st.warning(
                    "No watchlists available. Add stocks to create a watchlist.")
                return {}
    return {}

# Function to save watchlist to a JSON file


def save_watchlists(file_path, watchlists):
    with file_path.open('w') as file:
        json.dump(watchlists, file, indent=4)


# Load the CSV file

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

# Function to fetch stock prices and additional data using.history with 1-minute interval


def fetch_stock_data(symbols):
    stock_data = []
    for symbol in symbols:
        stock = yf.Ticker(symbol)
        # Fetch historical data for the last 1 day with 1-minute interval
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            latest = hist.iloc[-1]
            stock_data.append({
                'Name': stock.info.get('shortName', 'N/A'),
                'Current Price': latest['Close'],
                'Volume': latest['Volume'],
                'Open': latest['Open'],
                'Prev Close': hist.iloc[-2]['Close'] if len(hist) > 1 else 'N/A',
                'High (Day)': latest['High'],
                'Low (Day)': latest['Low'],
                'Last Trade Time': latest.name.time(),
                'Last Trade Date': latest.name.date(),
            })

    return pd.DataFrame(stock_data)


def create_styled_df(df):

    if not df.empty:
        last_trade_date = df['Last Trade Date'].iloc[0]
        st.write(f"Date: {last_trade_date}")
        df = df.drop(columns=['Last Trade Date'])

        column_formats = {
            'Current Price': '{:.2f}',
            'Volume': '{:,.0f}',
            'Open': '{:.2f}',
            'Prev Close': '{:.2f}' if 'Prev Close' in df.columns else None,
            'High (Day)': '{:.2f}',
            'Low (Day)': '{:.2f}',
        }

        def highlight_current_price(row):
            styles = [''] * len(row)
            current_price_idx = df.columns.get_loc('Current Price')
            if row['Current Price'] < row['Open']:
                styles[current_price_idx] = 'color: #f5651d; font-weight: bold'
            elif row['Current Price'] > row['Open']:
                styles[current_price_idx] = 'color:#04b568; font-weight: bold'
            return styles

        styled_df = (
            df.style
            .apply(highlight_current_price, axis=1)
            .format({col: fmt for col, fmt in column_formats.items() if fmt})
        )
        return styled_df


text = "Yahoo Finance price quote data is not real-time and may lag by up to 10 minutes.\n For the most current and accurate financial information, we recommend consulting a real-time data source."


@st.experimental_fragment
def fetch_and_display_price(selected_symbols):
    # symbols = [...]  # list of stock symbols
    stock_data = fetch_stock_data(selected_symbols)
    styled_df = create_styled_df(stock_data)
    if styled_df is not None:
        with st.container(height=350):

            st.markdown(
                f"""
                    <p style='color: #434a45; font-size: 10px;'>{text}</p>
                    """,
                unsafe_allow_html=True
            )
            st.write("")
            st.dataframe(styled_df, hide_index=True, use_container_width=True)

        if st.button("Refresh Price"):
            st.rerun()


# @st.cache_data
def fetch_info(symbol):
    stock = yf.Ticker(symbol)
    stock.get_analyst_price_target


# @st.cache_data
def fetch_earnings_calendar(_stock):
    data = _stock.get_calendar()
    df = pd.DataFrame(data)
    return df


# @st.cache_data
def fetch_recommendations(_stock):
    data = _stock.get_recommendations_summary()
    numeric_df = data.drop(columns=["period"])
    max_value = numeric_df.sum(axis=1).max()
    return data, numeric_df, max_value


# @st.cache_data
def plot_recommendations(data, numeric_df, max_value):

    # Create a stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 2))
    data.plot(kind="bar", stacked=True, ax=ax, color=[
        "#1b4ca1", "#5473a8", "#cccc00", "#d15b4d", "#bd3728"])
    ax.set_xlabel("Time Period", fontsize=5)
    ax.set_ylabel("Number of Recommendations", fontsize=5)
    # ax.set_xticklabels(["Current", "1 mth ago", "2 mths ago", "3 mths ago"], rotation=45, ha='right')
    ax.legend(loc="center left",
              bbox_to_anchor=(1, 0.5), fontsize=6)
    # Reduced font size for x-tick labels
    ax.tick_params(axis='x', labelsize=6)
    ax.tick_params(axis='y', labelsize=6)
    # Dynamically set the y-limit based on the max value in the data
    # Total recommendations for each time period
    max_value = numeric_df.sum(axis=1).max()
    # Add a 10% margin for better visualization
    ax.set_ylim(0, max_value * 1.1)
    for spine in ax.spines.values():
        spine.set_linewidth(0.2)  #
    # Make space for the legend
    plt.tight_layout(rect=[0, 0, 0.8, 1])
    st.pyplot(fig)
    plt.close(fig)


# @st.cache_data
def fetch_dividends(_stock):
    data = _stock.get_dividends()
    # Get the current date
    current_date = datetime.now()
    # Calculate the date 3 years ago
    three_years_ago = pd.Timestamp(
        current_date - timedelta(days=3 * 365)).tz_localize("America/New_York")

    # Filter the Series for rows from the past 3 years
    filtered_data = data[data.index >= three_years_ago]
    return filtered_data


# @st.cache_data
def plot_dividends(filtered_data):

    # Plot the filtered data
    plt.figure(figsize=(10, 4.5))
    plt.plot(filtered_data.index, filtered_data.values, marker='o',
             linestyle='-', color='b', label="Filtered Data")
    plt.title("Dividends for the Past 3 Years", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Dividends", fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)
    plt.close()


@st.cache_data
def fetch_upgrades_downgrades(_stock):
    data = _stock.get_upgrades_downgrades()
    return data


@st.cache_data
def plot_stock_data(symbol, period='1y'):
    """
    Fetches and plots the historical stock data for a given symbol and period.

    Parameters:
    symbol (str): The stock symbol (e.g., 'AAPL' for Apple Inc.).
    period (str): The time period for which to fetch the data (e.g., '1y' for one year).
    """
    # Fetch the stock data
    data = yf.Ticker(symbol).history(period=period)

    if data.empty:
        print(f"No data found for {symbol} over the period {period}.")
        return

    # Plot the closing prices
    plt.figure(figsize=(10, 4))  # Set the figure size
    # Plot the closing prices
    plt.plot(data.index, data['Close'], label='Close Price', color='b')
    plt.title(f'{symbol} Stock Price Over the Last {period}')  # Add a title
    plt.xlabel('Date')  # Label the x-axis
    plt.ylabel('Price')  # Label the y-axis
    plt.legend()  # Add a legend
    plt.grid(True)  # Add a grid
    st.pyplot(plt)
    plt.close()


def markdown_tab(text):

    st.markdown(
        f"""
        <h2 style='color:#737578; font-size: 16px;'>{text}</h2>
        """,
        unsafe_allow_html=True
    )


def check_folder(drive, parent_folder_id, user_email_prefix):
    query = f"'{parent_folder_id}' in parents and title='{user_email_prefix}' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        user_folder = file_list[0]
        # st.success(f"User folder '{user_email_prefix}' found.")
        return user_folder['id']
    else:
        st.warning(f"User folder '{user_email_prefix}' not found.")


def upload_to_drive(drive, local_path, parent_folder_id):
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            file_name = file_path.name
            file_obj = drive.CreateFile({
                'title': file_name,
                'parents': [{'id': parent_folder_id}]
            })
            file_obj.SetContentFile(str(file_path))
            file_obj.Upload()


def empty_folder(drive, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    for file in file_list:
        file_obj = drive.CreateFile({'id': file['id']})
        file_obj.Trash()


def upload_subfolders_to_drive(drive, local_path, user_folder_id):
    subfolders = ['watchlist', 'portfolio']
    for subfolder_name in subfolders:
        subfolder_path = local_path / subfolder_name
        if subfolder_path.exists():
            # Get the ID of the subfolder
            query = f"'{user_folder_id}' in parents and title='{subfolder_name}' and trashed=false"
            file_list = drive.ListFile({'q': query}).GetList()
            if file_list:
                subfolder_id = file_list[0]['id']
                # Empty the subfolder
                empty_folder(drive, subfolder_id)
            else:
                # Create the subfolder if it doesn't exist
                subfolder = drive.CreateFile({
                    'title': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [{'id': user_folder_id}]
                })
                subfolder.Upload()
                subfolder_id = subfolder['id']
            # Upload files to the subfolder
            upload_to_drive(drive, subfolder_path, subfolder_id)
        else:
            st.error(f"Subfolder '{subfolder_name}' not found.")


def upload_to_google_drive():
    try:
        drive = st.session_state.drive
        user_email_prefix = st.session_state.user_id
        local_path = pathlib.Path("./user_data") / user_email_prefix
        folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"
        user_folder_id = check_folder(
            drive, folder_id, user_email_prefix)
        upload_subfolders_to_drive(drive, local_path, user_folder_id)
    except Exception as e:
        st.error(f"Upload failed: {e}")
