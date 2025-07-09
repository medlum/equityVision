import yfinance as yf
import streamlit as st
from utils_markdown import display_md
import streamlit_antd_components as sac
import requests
import xml.etree.ElementTree as ET


def CNAheadlines(rss_url):

    
    # Fetch the RSS feed
    response = requests.get(rss_url)
    response.raise_for_status()

    # Parse the XML content
    root = ET.fromstring(response.content)

    # Find all <item> elements (RSS entries)
    items = root.findall(".//item")

    news = []

    # Loop through items and print title/link
    for i, item in enumerate(items):
        title = item.findtext("title")
        
        news.append(title)

    return ' ☛ '.join(news)

def breakingnews(results, label, variant):
    """
    creates news ticker with CNAheadlines tools from utils
    """
    sac.alert(label=label,
              description=results,
              size='sm',
              radius='0px',
              #color="#705302",
              #icon=True,
              variant=variant,
              closable=True,
              banner=[False, True])

#@st.cache_data
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
                results.append((name, f"{last_close:.2f}", f"{pct_change:.2f}%"))
                #change_symbol = "🔼" if change > 0 else "🔻" if change < 0 else ""
                #if change_symbol == "+":
                #    results.append(f" **{name} :** {last_close:.2f} {change_symbol}{abs(pct_change):.2f}%")
                #else:
                #    results.append(f" **{name} :** {last_close:.2f} {change_symbol}{abs(pct_change):.2f}%")
            else:
                results.append("Not enough data available.")
        except Exception as e:
            results[name] = {"Error": str(e)}
    
    return results
    #return ' | '.join(results)


# Example usage
# Index tickers
indices = {
    "Dow Jones".upper(): "^DJI", 
    "S&P 500".upper(): "^GSPC",
    "NASDAQ".upper(): "^IXIC",
    "Russell 2000".upper(): "^RUT",
    "VIX".upper(): "^VIX",
    "US Dollar Index".upper(): "DX-Y.NYB",
    "Crude Oil".upper(): "CL=F",
    "Gold".upper(): "GC=F",
    "FTSE 100".upper(): "^FTSE",
    "STI".upper(): "^STI",
    "Nikkei 225".upper(): "^N225",
    "Hang Seng".upper(): "^HSI",
    "EUR/USD": "EURUSD=X",
    "USD/GBP": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "USD/SGD": "SGD=X",
}
data = get_indices_data(indices)


# -----set up news ticker ------#
# RSS feed URL
rss_url = "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936"
news = CNAheadlines(rss_url)  # utils

#st.write(data)