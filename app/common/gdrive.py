import io
import logging
from fastapi import HTTPException, status
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
from getfilelistpy import getfilelist
import re
from google.oauth2 import service_account
from app.common.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

async def get_files_from_link(url: str):
    files_info = None
    gdrive_extracted_id, gdrive_url_type = get_gdrive_id_and_type(url)

    if gdrive_extracted_id:
        if gdrive_url_type == "folder":
            files_info = get_files_info_from_folder_id(gdrive_extracted_id)
        else:
            files_info = get_file_info_from_file_id(gdrive_extracted_id)
        
        if files_info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unable to fetch {gdrive_url_type} info from google drive (Please make sure the resource exists and has been shared publicly)")
        elif len(files_info) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unable to fetch {gdrive_url_type} info from google drive (File type not supported)")  
    else:
        logger.error("Please enter a valid google drive link")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid google drive link provided")

    downloaded_files = []
    for file_info in files_info:
        try:
            file_name, file_bytes, file_type = get_file_name_bytes_type(file_info)
            downloaded_files.append({"file_bytes": file_bytes, "file_name": file_name, "file_type": file_type})
        except Exception as ex:
            logger.error(f"Error occured while downloading file from google drive. File name: {files_info['name']} | Error: {ex}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"Error occured while downloading file from google drive. File name: {files_info['name']}")
    return downloaded_files

def get_gdrive_id_and_type(url:str):
    if url is None:
        return None, None

    patterns = [
        (r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/?", "file"),
        (r"https?://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)/?", "file"),
        (r"https?://drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)", "folder"),
        (r"https?://drive\.google\.com/drive/u/\d/folders/([a-zA-Z0-9_-]+)", "folder"),
        (r"https?://drive\.google\.com/.+/folders/([a-zA-Z0-9_-]+)", "folder")
    ]

    for pattern, type in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), type

    return None, None

def get_file_info_from_file_id(file_id:str):
    creds = service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS)

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
        logger.error(f"An error occurred: {error}")
        return None

def get_files_info_from_folder_id(folder_id:str):
    creds = service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS)
    
    try:
        service = build("drive", "v3", credentials=creds)
        res = service.files().get(fileId=folder_id, fields="id, name, mimeType", supportsAllDrives=True).execute()

        resource = {
            "service_account": creds,
            "id": folder_id,
            "fields": "files(id, name, mimeType)",
        }
        res = getfilelist.GetFileList(resource)
    except Exception as error:
        logger.error(f"An error occurred: {error}")
        return None

    if res is None or res.get("fileList") is None:
        logger.error(f"An error occurred: Unable to list files in folder")
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
    creds = service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS)

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
        logger.error(f"An error occurred: {error}")
        raise error

    return file

def get_google_supported_file_content(file_id):
    creds = service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS)

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
        logger.error(f"An error occurred: {error}")
        raise error

    return file

def get_file_content_string(file):
    file_content = None
    if file["mimeType"] == "application/vnd.google-apps.document":
        file_content = get_google_supported_file_content(file['id'])
        pdf_reader = PdfReader(file_content)
        file_content = '\n'.join([page.extract_text() for i, page in enumerate(pdf_reader.pages)])
    else:
        file_content = get_google_unsupported_file_content(file['id'])
        if (file["mimeType"] == "application/pdf"):
            pdf_reader = PdfReader(file_content)
            file_content = '\n'.join([page.extract_text() for i, page in enumerate(pdf_reader.pages)])
        else:
            file_content.seek(0)
            content_bytes = file_content.read()
            file_content = content_bytes.decode('utf-8')
    return file_content

def get_file_name_bytes_type(file):
    filecontent = None
    filetype = None
    filename = file["name"]

    # convert google docs document to pdf and pdf extension
    if file["mimeType"] == "application/vnd.google-apps.document":
        filecontent = get_google_supported_file_content(file['id'])
        filetype = "application/pdf"
        filename += ".pdf"
    else:
        filecontent = get_google_unsupported_file_content(file['id'])
        filetype = file["mimeType"]
    return filename, filecontent, filetype

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