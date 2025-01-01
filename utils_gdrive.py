
import pathlib
import streamlit as st
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

@st.cache_data
def load_data(file_path):
# Load the stock symbol and name from NYSE snd SGX csv 
    if file_path.exists():
        return pd.read_csv(file_path)
    else:
        st.warning("No csv file loaded")


def check_folder(service, parent_folder_id, user_id):
    query = f"'{parent_folder_id}' in parents and name='{user_id}' and trashed=false"
    try:
        response = service.files().list(q=query).execute()
        file_list = response.get('files', [])
        if file_list:
            user_folder = file_list[0]
            return user_folder['id']
        else:
            st.warning(f"User folder '{user_id}' not found.")
            return None
    except HttpError as error:
        st.warning(f"An error occurred: {error}")
        return None
    

def upload_to_drive(service, local_path, parent_folder_id):
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            file_name = file_path.name
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }
            media = MediaFileUpload(str(file_path), resumable=True)
            try:
                file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"File {file_name} uploaded with ID: {file.get('id')}")
            except HttpError as error:
                print(f"An error occurred: {error}")


def empty_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    try:
        response = service.files().list(q=query).execute()
        file_list = response.get('files', [])
        for file in file_list:
            service.files().update(fileId=file['id'], body={'trashed': True}).execute()
            #st.warning(f"File {file['name']} trashed.")
    except HttpError as error:
        st.warning(f"An error occurred: {error}")

def upload_subfolders_to_drive(service, local_path, user_folder_id):
    subfolders = ['watchlist', 'portfolio']
    for subfolder_name in subfolders:
        subfolder_path = local_path / subfolder_name
        if subfolder_path.exists():
            # Get the ID of the subfolder
            query = f"'{user_folder_id}' in parents and name='{subfolder_name}' and trashed=false"
            response = service.files().list(q=query).execute()
            file_list = response.get('files', [])
            if file_list:
                subfolder_id = file_list[0]['id']
                # Empty the subfolder
                empty_folder(service, subfolder_id)
            else:
                # Create the subfolder if it doesn't exist
                subfolder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [user_folder_id]
                }
                subfolder = service.files().create(body=subfolder_metadata, fields='id').execute()
                subfolder_id = subfolder['id']
                st.success(f"Subfolder {subfolder_name} created with ID: {subfolder_id}")
            # Upload files to the subfolder
            upload_to_drive(service, subfolder_path, subfolder_id)
        else:
            st.error(f"Subfolder '{subfolder_name}' not found.")


def upload_to_google_drive():
    try:
        drive = st.session_state.drive
        user_id = st.session_state.user_id
        local_path = pathlib.Path("./user_data") / user_id
        folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"
        user_folder_id = check_folder(
            drive, folder_id, user_id)
        upload_subfolders_to_drive(drive, local_path, user_folder_id)
    except Exception as e:
        st.error(f"Upload failed: {e}")
