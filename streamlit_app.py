import streamlit as st
from utils_entry_pt import *
# Configure the Streamlit app with a title, layout, icon, and initial sidebar state
st.set_page_config(page_title="Equity Trading",
                   layout="wide",
                   page_icon="💰",
                   initial_sidebar_state="expanded")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "drive" not in st.session_state:
    st.session_state.drive = None

if "drive_folder_id" not in st.session_state:
    st.session_state.drive_folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"


# set up nav page (login is located utils_entry_pt.py)
login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

backtest = st.Page("reports/backtest.py", 
                   title="Backtest", 
                   icon=":material/trending_up:", 
                   default=True)

watchlist = st.Page("reports/watchlist.py", 
                    title="Watchlist",
                    icon=":material/search:")

portfolio = st.Page("reports/portfolio.py", 
                    title="Portfolio",
                    icon=":material/summarize:")

search = st.Page("tools/search.py", 
                 title="Search", 
                 icon=":material/search:")
history = st.Page("tools/history.py", title="History",
                  icon=":material/history:")


if st.session_state.logged_in:

    pg = st.navigation(
        {
            "Account": [logout_page],
            "Dashboard": [backtest, watchlist, portfolio],
            "Tools": [search, history],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()

#bugs = st.Page("reports/bugs.py", title="Bug reports",
#               icon=":material/bug_report:")

#alerts = st.Page(
#    "reports/alerts.py", title="System alerts", icon=":material/notification_important:")

