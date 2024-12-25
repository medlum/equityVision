#import streamlit as st
import json
from pathlib import Path

def load_watchlists(file_path):
# Function to load watchlists from a JSON file
    if file_path.exists():
        with file_path.open('r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
            else:
                print(
                    "No watchlists available. Add stocks to create a watchlist.")
                return {}
    return {}

def save_watchlists(file_path, watchlists):
# Function to save watchlist to a JSON file
    with file_path.open('w') as file:
        json.dump(watchlists, file, indent=4)



watchlist_folder = Path(f'user_data/andy/watchlist')
watchlist_file_path = watchlist_folder / 'watchlist_SGX.json'
watchlist_folder.mkdir(parents=True, exist_ok=True)

watchlists = load_watchlists(watchlist_file_path)

save_watchlists(watchlist_file_path, watchlists)