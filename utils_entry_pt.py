from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import requests
import streamlit as st
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
# Function to authenticate with Google Drive and fetch the user's email address


def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/userinfo.email']
    # Check if credentials are already available
    if 'credentials' not in st.session_state:
        # Create the flow using the client secrets file from the Google API Console
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            SCOPES,
            redirect_uri='https://equity-vision.streamlit.app'
        )

        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        # Store the state in session state
        st.session_state.state = state

        # Redirect the user to the authorization URL
        st.write(
            f"Please go to this URL to authorize: [Authorize]({authorization_url})")
        return None, None

    # Get the authorization response
    if 'code' in st.experimental_get_query_params():
        code = st.experimental_get_query_params()['code'][0]
        state = st.experimental_get_query_params()['state'][0]

        # Exchange the authorization code for credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            SCOPES,
            state=st.session_state.state,
            redirect_uri='https://<your-app-name>.streamlit.app/callback'
        )
        flow.fetch_token(code=code)

        # Save the credentials in session state
        creds = flow.credentials
        st.session_state.credentials = creds

    # Get the credentials from session state
    creds = st.session_state.credentials

    # Build the Google Drive service
    drive_service = build('drive', 'v3', credentials=creds)

    # Get user info
    user_info = get_user_info(creds.token)
    user_email = user_info.get("email", "Unknown User")

    return drive_service, user_email

# def authenticate_google_drive():
#    gauth = GoogleAuth()
#    gauth.LoadClientConfigFile("client_secrets.json")
#    gauth.settings['oauth_scope'] = [
#        'https://www.googleapis.com/auth/drive',
#        'https://www.googleapis.com/auth/userinfo.email'
#    ]
#    gauth.LocalWebserverAuth()
#    access_token = gauth.credentials.access_token
#    user_info = get_user_info(access_token)
#    user_email = user_info.get("email", "Unknown User")
#    drive = GoogleDrive(gauth)
#    return drive, user_email

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
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    for file in file_list:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            folder_path = local_path / file['title']
            folder_path.mkdir(parents=True, exist_ok=True)
            download_drive_contents(drive, file['id'], folder_path)
        else:
            file_obj = drive.CreateFile({'id': file['id']})
            file_path = local_path / file['title']
            file_obj.GetContentFile(str(file_path))

# Function to check if user's folder exists and create if not


def check_and_create_user_folder(drive, parent_folder_id, user_email_prefix):
    query = f"'{parent_folder_id}' in parents and title='{user_email_prefix}' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        user_folder = file_list[0]
        # st.success(f"User folder '{user_email_prefix}' found.")
        return user_folder['id']
    else:
        st.info(
            f"User folder '{user_email_prefix}' not found. Creating now...")
        user_folder = drive.CreateFile({
            'title': user_email_prefix,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': parent_folder_id}]
        })
        user_folder.Upload()
        st.success(f"User folder '{user_email_prefix}' created.")

        # Create subfolders: watchlist and portfolio
        for subfolder_name in ['watchlist', 'portfolio']:
            subfolder = drive.CreateFile({
                'title': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': user_folder['id']}]
            })
            subfolder.Upload()
            st.success(f"Subfolder '{subfolder_name}' created.")

        return user_folder['id']

# Main login function to handle user authentication in the Streamlit app


def login():
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title(":rainbow[EquityVision]")
        app_description = f"""
        EquityVision is a powerful platform for investors and traders, offering backtesting tools
        to evaluate trading strategies, portfolio tracking to monitor returns, and watchlist creation
        to track favorite stocks. An integrated chatbot provides real-time assistance and insights,
        empowering users to make smarter investment decisions."""
        st.markdown(f"""
            <p style='color:#737578; font-size: 16px; text-align: justify'>{app_description}</p>
            """, unsafe_allow_html=True)
        # with st.sidebar:
        # st.write("**Authenticate with Google Drive**")
        if st.button(":blue[**Authenticate with Google Drive**]"):
            try:
                with st.spinner("Setting up..."):
                    drive, user_email = authenticate_google_drive()
                    st.session_state.logged_in = True
                    st.session_state.drive = drive
                    st.session_state.user_email = user_email
                    st.success(f"Successfully authenticated as: {user_email}")

                    folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"
                    # Use the prefix before '@' as folder name
                    user_email_prefix = user_email.split('@')[0]
                    local_path = Path("./user_data") / user_email_prefix
                    local_path.mkdir(parents=True, exist_ok=True)

                    user_folder_id = check_and_create_user_folder(
                        drive, folder_id, user_email_prefix)

                    download_drive_contents(drive, user_folder_id, local_path)
                    # st.success(f"Successfully downloaded to: {local_path}")

                    st.session_state.logged_in = True
                    st.session_state.user_id = user_email_prefix
                    st.rerun()

            except Exception as e:
                st.error(f"Authentication failed: {e}")


def logout():
    # if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.rerun()
