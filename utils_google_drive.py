import streamlit as st
from pathlib import Path
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Authenticate Google Drive


@st.cache_resource
def authenticate_google_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_drive_folder_contents(drive, parent_folder_id):
    """
    Retrieve a dictionary of existing folders/files in Google Drive under the given parent folder.
    Keys are names of files/folders, and values are their Google Drive IDs.
    """
    query = f"'{parent_folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    drive_contents = {}
    for file in file_list:
        drive_contents[file['title']] = {
            'id': file['id'], 'mimeType': file['mimeType']}
    return drive_contents


def upload_or_overwrite_files(drive, local_folder: Path, parent_folder_id: str):
    """
    Compare local folders/files with Google Drive contents, upload new files,
    and overwrite existing files in Drive.
    """
    folder_map = {str(local_folder): parent_folder_id}

    for path in local_folder.rglob("*"):
        parent_path = str(path.parent)
        parent_id = folder_map[parent_path]

        if path.is_dir():
            # Fetch existing folders in the parent Drive folder
            drive_contents = get_drive_folder_contents(drive, parent_id)

            if path.name in drive_contents:
                st.info(f"Folder already exists in Drive: {path}")
                folder_id = drive_contents[path.name]['id']
            else:
                # Create new folder
                folder_metadata = {
                    "title": path.name,
                    "parents": [{"id": parent_id}],
                    "mimeType": "application/vnd.google-apps.folder"
                }
                folder = drive.CreateFile(folder_metadata)
                folder.Upload()
                folder_id = folder['id']
                st.success(f"Created folder in Drive: {path}")

            folder_map[str(path)] = folder_id

        else:
            # Fetch existing files in the parent Drive folder
            drive_contents = get_drive_folder_contents(drive, parent_id)

            if path.name in drive_contents:
                # Overwrite existing file content
                file_id = drive_contents[path.name]['id']
                gfile = drive.CreateFile({'id': file_id})
                gfile.SetContentFile(str(path))
                gfile.Upload()
                st.warning(f"Overwritten existing file: {path}")
            else:
                # Upload new file
                file_metadata = {
                    "title": path.name,
                    "parents": [{"id": parent_id}]
                }
                gfile = drive.CreateFile(file_metadata)
                gfile.SetContentFile(str(path))
                gfile.Upload()
                st.success(f"Uploaded new file to Drive: {path}")


def main():
    st.title("Upload and Overwrite Files in Google Drive")

    # Input for username
    username = st.text_input("Enter your username:")

    if st.button("Upload and Overwrite Files to Google Drive"):
        if username:
            user_data_folder = Path("user_data")

            if user_data_folder.exists() and user_data_folder.is_dir():
                try:
                    # Authenticate Google Drive
                    drive = authenticate_google_drive()

                    # Replace with your Drive folder ID
                    parent_drive_folder_id = "19OEoGnaj2aE4edVMVvA8eHdF7BI_7H4x"

                    # Step 1: Compare and upload/overwrite files
                    upload_or_overwrite_files(
                        drive, user_data_folder, parent_drive_folder_id)

                    st.success("Files uploaded and overwritten successfully!")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            else:
                st.error(
                    "The folder 'user_data' does not exist or is not a directory.")
        else:
            st.error("Please enter a username.")


if __name__ == "__main__":
    main()
