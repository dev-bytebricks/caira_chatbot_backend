import io
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
import streamlit as st
from getfilelistpy import getfilelist
import re
from google.oauth2 import service_account

SERVICE_ACCOUNT = st.session_state.global_config["Service_Account_Key"]

def get_gdrive_id_and_type(url:str):
    if url is None:
        return None, None

    patterns = [
        (r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/?", "file"),
        (r"https?://drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)", "folder"),
        (r"https?://drive\.google\.com/drive/u/\d/folders/([a-zA-Z0-9_-]+)", "folder"),
        (r"https?://drive\.google\.com/.+/folders/([a-zA-Z0-9_-]+)", "folder"),
    ]

    for pattern, type in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), type

    return None, None

def get_file_info_from_file_id(file_id:str):
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT)

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)
        response = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        if response:
            mimeType = str(response.get("mimeType"))
            if mimeType is not None and ('text/' in mimeType or mimeType == 'application/pdf' or mimeType == 'application/vnd.google-apps.document'):
                return [response]
        return []
    except HttpError as error:
        st.error(f"An error occurred: {error}")
        return None

def get_files_info_from_folder_id(folder_id:str):
    try:
        # check if folder is accesible
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT)
        service = build("drive", "v3", credentials=creds)
        res = service.files().get(fileId=folder_id, fields="id, name, mimeType", supportsAllDrives=True).execute()

        resource = {
            "service_account": creds,
            "id": folder_id,
            "fields": "files(id, name, mimeType)",
        }
        res = getfilelist.GetFileList(resource)
    except Exception as error:
        st.error(f"An error occurred: {error}")
        return None

    if res is None or res.get("fileList") is None:
        st.error(f"An error occurred: Unable to list files in folder")
        return None
    
    finalFilesList = []
    for innerdict in res.get("fileList"):
        if innerdict is not None and innerdict.get("files") is not None:
            filesList = innerdict.get("files")
            for file in filesList:
                mimeType = str(file.get("mimeType"))
                if mimeType is not None and ('text/' in mimeType or mimeType == 'application/pdf' or mimeType == 'application/vnd.google-apps.document'):
                    finalFilesList.append(file)

    return finalFilesList

def get_google_unsupported_file_content(file_id):
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT)

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

    except HttpError as error:
        st.error(f"An error occurred: {error}")
        file = None

    return file.getvalue()

def get_google_supported_file_content(file_id):
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT)

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)
        request = service.files().export_media(
        fileId=file_id, mimeType="application/pdf"
        )
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

    except HttpError as error:
        st.write(f"An error occurred: {error}")
        file = None

    return file.getvalue()

def get_file_content(file):
    filecontent = None
    if file["mimeType"] == "application/vnd.google-apps.document":
        filecontent = get_google_supported_file_content(file['id'])
        pdf_reader = PdfReader(io.BytesIO(filecontent))
        filecontent = '\n'.join([page.extract_text() for i, page in enumerate(pdf_reader.pages)])
    else:
        filecontent = get_google_unsupported_file_content(file['id'])
        if (file["mimeType"] == "application/pdf"):
            pdf_reader = PdfReader(io.BytesIO(filecontent))
            filecontent = '\n'.join([page.extract_text() for i, page in enumerate(pdf_reader.pages)])
        else:
            filecontent = str(filecontent, 'utf-8')
    return filecontent

def display_file_info(file):
    filetype = file["mimeType"]
    if file["mimeType"] == "application/vnd.google-apps.document":
        filetype = "Google Docs"
    if 'text/' in file["mimeType"]:
        filetype = str(file["mimeType"])
        filetype = filetype.removeprefix("text/").upper()
    if file["mimeType"] == "application/pdf":
        filetype = "PDF"
    return f"{file['name']} ({filetype})"