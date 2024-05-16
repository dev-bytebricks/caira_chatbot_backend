import logging
from fastapi import HTTPException, status
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from getfilelistpy import getfilelist
import re
from google.oauth2 import service_account
from app.common.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

SERVICE = build("drive", 
                "v3", 
                credentials=service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS))

async def get_files_info_from_link(url: str):
    files_info = None
    gdrive_extracted_id, gdrive_url_type = _get_gdrive_id_and_type(url)

    if gdrive_extracted_id:
        if gdrive_url_type == "folder":
            files_info = _get_files_info_from_folder_id(gdrive_extracted_id)
        else:
            files_info = _get_file_info_from_file_id(gdrive_extracted_id)
        
        if files_info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unable to fetch {gdrive_url_type} info from google drive (Please make sure the resource exists and has been shared publicly)")
        elif len(files_info) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unable to fetch {gdrive_url_type} info from google drive (File type not supported)")  
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid google drive link provided")

    return files_info

def _get_gdrive_id_and_type(url:str):
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

def _get_file_info_from_file_id(file_id:str):
    try:
        response = SERVICE.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        if response:
            mimeType = str(response.get("mimeType"))
            if mimeType is not None and ('text/' in mimeType or mimeType == 'application/pdf' or mimeType == 'application/vnd.google-apps.document'):
                return [response]
        return []
    except HttpError as error:
        logger.exception(f"An error occurred: {error}")
        return None

def _get_files_info_from_folder_id(folder_id:str):
    try:
        resource = {
            "service_account": service_account.Credentials.from_service_account_info(settings.GOOGLE_SERVICE_ACCOUNT_CREDS),
            "id": folder_id,
            "fields": "files(id, name, mimeType)",
        }
        res = getfilelist.GetFileList(resource)
    except Exception as error:
        logger.exception(f"An error occurred: {error}")
        return None

    if res is None or res.get("fileList") is None:
        logger.exception(f"An error occurred: Unable to list files in folder")
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