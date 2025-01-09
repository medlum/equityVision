import yfinance as yf
import streamlit as st
from utils_markdown import display_md
import streamlit_antd_components as sac
import requests

from bs4 import BeautifulSoup
def CNAheadlines(genre: str):

    url = "https://www.channelnewsasia.com"
    response = requests.get(url)
    if response.status_code == 200:
        news = []
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = soup.find('body').find_all('h6')  # headlines at h6
        for x in headlines:
            news.append(x.text.strip())
        return '. '.join(news)
    else:
        return "No response from news provider."

def breakingnews(results, label, variant):
    """
    creates news ticker with CNAheadlines tools from utils
    """
    sac.alert(label=label,
              description=results,
              size='xs',
              radius='0px',
              color="#205699",
              # icon=True,
              variant=variant,
              closable=True,
              banner=[False, True])


def get_indices_data(indices, days=5):
    """
    Fetch the last and previous closing prices for multiple indices.

    Parameters:
    - indices: Dictionary with index/commodity names as keys and tickers as values.
    - days: Number of past days to fetch data for (default is 5).

    Returns:
    - A dictionary with index names as keys and data including last close, 
      previous close, difference, and percentage difference as values.
    """
    results = []

    for name, ticker in indices.items():
        try:
            # Fetch historical data
            data = yf.Ticker(ticker).history(period=f"{days}d")

            if len(data) >= 2:
                last_close = data['Close'].iloc[-1]
                previous_close = data['Close'].iloc[-2]
                change = last_close - previous_close
                pct_change = (change / previous_close) * 100
                change_symbol = "🔺" if change > 0 else "🔻" if change < 0 else ""
                if change_symbol == "+":
                    results.append(f" **{name} :** {last_close:.2f} {change_symbol}{abs(pct_change):.2f}%")
                else:
                    results.append(f" **{name} :** {last_close:.2f} {change_symbol}{abs(pct_change):.2f}%")
            else:
                results.append("Not enough data available.")
        except Exception as e:
            results[name] = {"Error": str(e)}

    return '   '.join(results)

# Example usage
# Index tickers
indices = {
    "Dow Jones": "^DJI", 
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
    "US Dollar Index": "DX-Y.NYB",
    "Crude Oil": "CL=F",
    "Gold": "GC=F",
    "FTSE 100": "^FTSE",
    "STI": "^STI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "EUR/USD": "EURUSD=X",
    "USD/GBP": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "USD/SGD": "SGD=X",
}
data = get_indices_data(indices)

#breakingnews(data, '', 'filled')  # component_sidebar

# -----set up news ticker ------#
news = CNAheadlines("news")  # utils
#breakingnews(news, 'Breaking News...', 'outlined')  # component_sidebar


