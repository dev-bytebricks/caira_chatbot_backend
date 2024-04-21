import json
import logging
from typing import List
from fastapi import HTTPException, status
from app.common.settings import get_settings
from app.models.user import UserDocument
from app.schemas.responses.user_document import FileInfo, GdriveUploadResponse, DeleteDocumentsResponse, DocumentsListResponse, ValidateDocumentsResponse, FileExists
from app.common import gdrive, azurecloud
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

settings = get_settings()

logger = logging.getLogger(__name__)

async def enqueue_gdrive_upload(gdrivelink, username, session: Session):
    files_info = await gdrive.get_files_info_from_link(gdrivelink)

    # if len(files_info) > 20:
    #      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max 20 files are allowed per Google Drive link")

    unique_files = {}
    for file_info in files_info:
        file_name = file_info["name"]
        # Add file info to the dictionary if the name has not been added yet
        if file_name not in unique_files:
            unique_files[file_name] = file_info

    # Now unique_files contains only one entry per file name
    files_info = list(unique_files.values()) 

    failed_files = []
    files_to_enqueue = []

    # check if file is already uploaded
    for file_info in files_info:
        file_name = file_info["name"]
        file_type = file_info["mimeType"]
        if file_type == "application/vnd.google-apps.document":
            file_name += ".pdf"
        
        # check if file exists in database
        user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
            .filter(UserDocument.user_id == username, 
                UserDocument.document_name == file_name,
                UserDocument.status != "del_failed").first()
        if user_doc:
            # add logging for multiple statuses here (for completed status show same file exists but for other statuses show file upload is in progress)
            # for to_delete status, we can say try again later
            failed_files.append(FileInfo(filename=file_name, error="File with same name already exists"))
        else:
            files_to_enqueue.append(file_info)

    if len(files_to_enqueue) == 0:
        return GdriveUploadResponse(queued_files=[], failed_files=failed_files)

    messages = []
    for batch in _chunk_data(files_to_enqueue, size=20):
        message_body = json.dumps({"user_name": username, "files_info": batch})
        messages.append(message_body)
    failed_messages = await azurecloud.send_messages_to_queue(settings.AZURE_STORAGE_CONSUMER_GDRIVE_UPLOAD_QUEUE_NAME, messages)

    for msg, error in failed_messages:
        failed_files_info = json.loads(msg)["files_info"]
        files_to_enqueue = [item for item in files_to_enqueue if item not in failed_files_info]
        failed_files.extend([FileInfo(filename=failed_file_info["name"], error=error) for failed_file_info in failed_files_info])
    
    queued_files = []
    # create file entry with transferring status for files in db
    for file_to_enqueue in files_to_enqueue:
        file_name = file_to_enqueue["name"]
        file_type = file_to_enqueue["mimeType"]
        if file_type == "application/vnd.google-apps.document":
            file_name += ".pdf"
        session.add(UserDocument(user_id=username, document_name=file_name, content_type=file_type, status="Transferring From Google Drive"))
        session.commit()
        queued_files.append(FileInfo(filename=file_name, status="Transferring From Google Drive"))

    return GdriveUploadResponse(queued_files=queued_files, failed_files=failed_files)

async def get_download_link(username, file_name, session: Session):
    file_not_found_exec = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # check if file exists in database with completed status
    user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
        .filter(UserDocument.user_id == username, 
                UserDocument.document_name == file_name,
                UserDocument.status == "Completed").first()

    if not user_doc:
        raise file_not_found_exec

    download_link = await azurecloud.get_download_link(username, file_name)
    if download_link is None:
        raise file_not_found_exec
    
    return {"download_link": download_link}

async def get_azure_storage_token():
    token = azurecloud.get_container_sas()
    return {"azure_storage_token": token}

async def get_documents_list(username, session: Session):
    user_docs = session.query(UserDocument).options(joinedload(UserDocument.user))\
        .filter(
            UserDocument.user_id == username,
            UserDocument.status != "del_failed",
            UserDocument.status != "to_delete"
            ).order_by(desc(UserDocument.created_at)).all()
    
    # Clean up upload_failed docs after sending them
    session.query(UserDocument).options(joinedload(UserDocument.user))\
        .filter(
            UserDocument.user_id == username, 
            UserDocument.status == "upload_failed"
            ).delete(synchronize_session='fetch')
    session.commit()
    
    files = []
    failed_files = []

    for user_doc in user_docs:
        if user_doc.status == "upload_failed":
            failed_files.append(FileInfo(filename=user_doc.document_name, content_type=user_doc.content_type, status="Failed to process file"))
        else:
            files.append(FileInfo(filename=user_doc.document_name, content_type=user_doc.content_type, status=user_doc.status))

    return DocumentsListResponse(files=files, failed_files=failed_files)

async def enqueue_file_deletions(username, file_names: List[str], session: Session):
    failed_files = []
    existing_file_names = []

    for file_name in file_names:
       # check if file exists in database with completed status
        user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
            .filter(UserDocument.user_id == username, 
                UserDocument.document_name == file_name,
                UserDocument.status == "Completed").first()
        if user_doc:
            existing_file_names.append(file_name)
        else:
            # error logging can be made more descriptive using status
            failed_files.append(FileInfo(filename=file_name, error="File does not exists"))

    messages_to_enqueue = []
    for batch in _chunk_data(existing_file_names, size=256):
        message_body = json.dumps({"user_name": username, "file_names": batch})
        messages_to_enqueue.append(message_body)
    failed_messages = await azurecloud.send_messages_to_queue(settings.AZURE_STORAGE_CONSUMER_FILE_DELETE_QUEUE_NAME, messages_to_enqueue)
    
    sucessfully_queued_messages = messages_to_enqueue

    for msg, error in failed_messages:
        sucessfully_queued_messages.remove(msg)
        failed_file_names = json.loads(msg)["file_names"]
        failed_files.extend([FileInfo(filename=failed_file_name, error=error) for failed_file_name in failed_file_names])

    # update file status to "to_delete" in database
    for msg in sucessfully_queued_messages:
        for queued_file_name in json.loads(msg)["file_names"]:
            user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
                .filter(
                    UserDocument.user_id == username, 
                    UserDocument.document_name == queued_file_name).first()
            user_doc.status = "to_delete"
            session.add(user_doc)
            session.commit()

    return DeleteDocumentsResponse(failed_files=failed_files)

def _chunk_data(list, size):
    for i in range(0, len(list), size):
        yield list[i:i + size]

async def validate_filenames(username, file_names: List[str], session: Session):
    if len(file_names) == 0:
        return ValidateDocumentsResponse(files=[])

    existing_files = session.query(UserDocument)\
        .options(joinedload(UserDocument.user))\
        .filter(UserDocument.user_id == username, 
                UserDocument.document_name.in_(file_names), 
                UserDocument.status != "del_failed")\
        .all()
    
    existing_file_set = {doc.document_name for doc in existing_files}

    return ValidateDocumentsResponse(files=[FileExists(filename=file_name, exists=file_name in existing_file_set) for file_name in file_names])