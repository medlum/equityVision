from googleapiclient.http import MediaIoBaseDownload
import pathlib
import io
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import requests
import streamlit as st
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils_banner import breakingnews, data



app_description = f"""
        EquityVision is an equity platform for investors and traders, offering backtesting tools
        to evaluate trading strategies, portfolio tracking to monitor returns, and watchlist creation
        to track favorite stocks. A state of the art chatbot is integerated to provide real-time assistance and insights,
        empowering users to make smarter investment decisions."""

#PARENT_FOLDER_ID = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"


def get_gdrive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": st.secrets.service_account.project_id,
            "private_key_id": st.secrets.service_account.private_key_id,
            "private_key": st.secrets.service_account.private_key,
            "client_email": st.secrets.service_account.client_email,
            "client_id": st.secrets.service_account.client_id,
            "auth_uri": st.secrets.service_account.auth_uri,
            "token_uri": st.secrets.service_account.token_uri,
            "auth_provider_x509_cert_url": st.secrets.service_account.auth_provider_x509_cert_url,
            "client_x509_cert_url": st.secrets.service_account.client_x509_cert_url,
            "universe_domain": st.secrets.service_account.universe_domain,
        },
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

# Helper function to fetch the user's email from Google API using the access token


def get_user_info(access_token):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch user info. Ensure proper OAuth scopes.")
        return {}


# Function to download drive contents


def download_drive_contents(drive, folder_id, local_path):
    local_path = pathlib.Path(local_path)
    query = f"'{folder_id}' in parents and trashed=false"
    response = drive.files().list(q=query).execute()
    file_list = response.get('files', [])

    for file in file_list:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            folder_path = local_path / file['name']
            folder_path.mkdir(parents=True, exist_ok=True)
            download_drive_contents(drive, file['id'], folder_path)
        else:
            file_id = file['id']
            file_name = file['name']
            request = drive.files().get_media(fileId=file_id)
            file_path = local_path / file_name

            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    st.info(f"Download {int(status.progress() * 100)}%.")

            st.success(f"File '{file_name}' downloaded.")
# Function to check if user's folder exists and create if not


def check_and_create_user_folder(drive, parent_folder_id, user_id):
    query = f"'{parent_folder_id}' in parents and name='{user_id}' and trashed=false"
    response = drive.files().list(q=query).execute()
    file_list = response.get('files', [])

    if file_list:
        user_folder = file_list[0]
        # st.success(f"User folder '{user_id}' found.")
        return user_folder['id']
    else:
        st.info(
            f"User folder '{user_id}' not found. Creating now...")
        user_folder_metadata = {
            'name': user_id,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        user_folder = drive.files().create(body=user_folder_metadata).execute()
        st.success(f"User folder '{user_id}' created.")

        # Create subfolders: watchlist and portfolio
        for subfolder_name in ['watchlist', 'portfolio']:
            subfolder_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [user_folder['id']]
            }
            subfolder = drive.files().create(body=subfolder_metadata).execute()
            st.success(f"Subfolder '{subfolder_name}' created.")

        return user_folder['id']


def find_user_credentials(user_id, password):
    users = st.secrets["users"]
    for user in users:
        if user['user_id'] == user_id and user['password'] == password:
            return True

    return None

# Main login function to handle user authentication in the Streamlit app


def login():
    col1, col2, col3 = st.columns(3)
    with col2:
        breakingnews(data, '', 'light') 
        st.title(":rainbow[EquityVision]")

        st.markdown(f"""
            <p style='color:#737578; font-size: 16px; text-align: justify'>{app_description}</p>
            """, unsafe_allow_html=True)

        # User input for login
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        login_state = find_user_credentials(user_id, password)

        if login_state:
            with st.status("Logging in...", expanded=True):
                drive = get_gdrive_service()
                st.session_state.logged_in = True
                st.session_state.drive = drive
                st.session_state.user_id = user_id
                st.success(f"Successfully authenticated as: {user_id}")

                folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"
                local_path = Path("./user_data") / user_id
                local_path.mkdir(parents=True, exist_ok=True)

                user_folder_id = check_and_create_user_folder(
                    drive, folder_id, user_id)

                download_drive_contents(drive, user_folder_id, local_path)
                st.success(f"Successfully downloaded to: {local_path}")
                st.rerun()



def logout():
    # if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()
