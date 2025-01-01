import pathlib
import json
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils_markdown import display_md

def load_watchlists(file_path):
# Function to load watchlists from a JSON file
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


def save_watchlists(file_path, watchlists):
# Function to save watchlist to a JSON file
    #if file_path.exists():
    with file_path.open('w') as file:
        json.dump(watchlists, file, indent=4)
    #else:
    #    st.warning("No watchlists saved locally")

#@st.cache_data
#def load_data(file_path):
## Load the stock symbol and name from NYSE snd SGX csv 
#    if file_path.exists():
#        return pd.read_csv(file_path)
#    else:
#        st.warning("No csv file loaded")



def fetch_stock_data(symbols):
# Function to fetch stock prices and additional data using.history with 1-minute interval
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
        
        else:
            st.warning("No stock data appended")

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




@st.fragment
def fetch_and_display_price(selected_symbols):
    #display stock data in data frame
    stock_data = fetch_stock_data(selected_symbols)
    styled_df = create_styled_df(stock_data)

    if styled_df is not None:
        with st.container(height=350):
            text = """Yahoo Finance price quote data is not real-time and 
            may lag by up to 10 minutes.\n For the most current and accurate 
            financial information, we recommend consulting a real-time data source.
            """
            display_md.display(text, color="#434a45", font_size="10px", tag='p')
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
    return data


# @st.cache_data
def fetch_recommendations(_stock):
    data = _stock.get_recommendations_summary()
    if data.empty:
        #st.warning("No Recommendations found")
        return None, None, None 
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
    three_years_ago = pd.Timestamp(current_date - timedelta(days=3 * 365))

    # Ensure three_years_ago is timezone-aware
    if data.empty:
        # If the data is empty, return an empty Series
        return pd.Series(dtype=float)

    # Check if the data index is timezone-aware
    if data.index.tz is not None:
        three_years_ago = three_years_ago.tz_localize(data.index.tz)
    else:
        three_years_ago = three_years_ago.tz_localize("America/New_York")

    # Check the minimum date in the dataset
    min_date = data.index.min()

    # Use the later of the two dates as the starting point for filtering
    start_date = max(min_date, three_years_ago)

    # Filter the Series for rows from the start_date onwards
    filtered_data = data[data.index >= start_date]

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



#def check_folder(service, parent_folder_id, user_id):
#    query = f"'{parent_folder_id}' in parents and name='{user_id}' and trashed=false"
#    try:
#        response = service.files().list(q=query).execute()
#        file_list = response.get('files', [])
#        if file_list:
#            user_folder = file_list[0]
#            return user_folder['id']
#        else:
#            st.warning(f"User folder '{user_id}' not found.")
#            return None
#    except HttpError as error:
#        st.warning(f"An error occurred: {error}")
#        return None
#    
#
#def upload_to_drive(service, local_path, parent_folder_id):
#    for file_path in local_path.rglob('*'):
#        if file_path.is_file():
#            file_name = file_path.name
#            file_metadata = {
#                'name': file_name,
#                'parents': [parent_folder_id]
#            }
#            media = MediaFileUpload(str(file_path), resumable=True)
#            try:
#                file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
#                print(f"File {file_name} uploaded with ID: {file.get('id')}")
#            except HttpError as error:
#                print(f"An error occurred: {error}")
#
#
#def empty_folder(service, folder_id):
#    query = f"'{folder_id}' in parents and trashed=false"
#    try:
#        response = service.files().list(q=query).execute()
#        file_list = response.get('files', [])
#        for file in file_list:
#            service.files().update(fileId=file['id'], body={'trashed': True}).execute()
#            st.warning(f"File {file['name']} trashed.")
#    except HttpError as error:
#        st.warning(f"An error occurred: {error}")
#
#def upload_subfolders_to_drive(service, local_path, user_folder_id):
#    subfolders = ['watchlist', 'portfolio']
#    for subfolder_name in subfolders:
#        subfolder_path = local_path / subfolder_name
#        if subfolder_path.exists():
#            # Get the ID of the subfolder
#            query = f"'{user_folder_id}' in parents and name='{subfolder_name}' and trashed=false"
#            response = service.files().list(q=query).execute()
#            file_list = response.get('files', [])
#            if file_list:
#                subfolder_id = file_list[0]['id']
#                # Empty the subfolder
#                empty_folder(service, subfolder_id)
#            else:
#                # Create the subfolder if it doesn't exist
#                subfolder_metadata = {
#                    'name': subfolder_name,
#                    'mimeType': 'application/vnd.google-apps.folder',
#                    'parents': [user_folder_id]
#                }
#                subfolder = service.files().create(body=subfolder_metadata, fields='id').execute()
#                subfolder_id = subfolder['id']
#                print(f"Subfolder {subfolder_name} created with ID: {subfolder_id}")
#            # Upload files to the subfolder
#            upload_to_drive(service, subfolder_path, subfolder_id)
#        else:
#            st.error(f"Subfolder '{subfolder_name}' not found.")
#
#
#def upload_to_google_drive():
#    try:
#        drive = st.session_state.drive
#        user_id = st.session_state.user_id
#        local_path = pathlib.Path("./user_data") / user_id
#        folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"
#        user_folder_id = check_folder(
#            drive, folder_id, user_id)
#        upload_subfolders_to_drive(drive, local_path, user_folder_id)
#    except Exception as e:
#        st.error(f"Upload failed: {e}")
