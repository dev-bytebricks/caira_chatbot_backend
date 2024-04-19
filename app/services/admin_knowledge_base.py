import json
import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy import desc
from app.common.settings import get_settings
from app.models.user import KnowledgeBaseDocument
from app.schemas.responses.admin_knowledge_base import FileInfo, GdriveUploadResponse, DeleteDocumentsResponse, DocumentsListResponse
from app.common import gdrive, azurecloud
from sqlalchemy.orm import Session

settings = get_settings()

logger = logging.getLogger(__name__)

async def enqueue_gdrive_upload(gdrivelink, session: Session):
    files_info = await gdrive.get_files_info_from_link(gdrivelink)

    if len(files_info) > 200:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max 200 files are allowed per Google Drive link")

    failed_files = []
    files_to_enqueue = []

    # check if file is already uploaded
    for file_info in files_info:
        file_name = file_info["name"]
        file_type = file_info["mimeType"]
        if file_type == "application/vnd.google-apps.document":
            file_name += ".pdf"
        if _is_document_in_db(file_name, session):
            failed_files.append(FileInfo(filename=file_name, error="File with same name already exists"))
        else:
            files_to_enqueue.append(file_info)

    if len(files_to_enqueue) == 0:
        return GdriveUploadResponse(queued_files=[], failed_files=failed_files)

    messages = []
    for batch in _chunk_data(files_to_enqueue, size=5):
        message_body = json.dumps({"files_info": batch})
        messages.append(message_body)
    failed_messages = await azurecloud.send_messages_to_queue(settings.AZURE_STORAGE_KNOWLEDGEBASE_GDRIVE_UPLOAD_QUEUE_NAME, messages)
    
    if len(failed_messages) == 0:
        return GdriveUploadResponse(queued_files=[FileInfo(filename=file_to_enqueue["name"]) for file_to_enqueue in files_to_enqueue], 
                                    failed_files=[])

    for msg, error in failed_messages:
        failed_files_info = json.loads(msg)["files_info"]
        files_to_enqueue = [item for item in files_to_enqueue if item not in failed_files_info]
        failed_files.extend([FileInfo(filename=failed_file_info["name"], error=error) for failed_file_info in failed_files_info])
    return GdriveUploadResponse(queued_files=[FileInfo(filename=file_to_enqueue["name"]) for file_to_enqueue in files_to_enqueue], 
                                failed_files=failed_files)

async def get_download_link(file_name, session: Session):
    file_not_found_exec = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not _is_document_in_db(file_name, session):
        raise file_not_found_exec

    download_link = await azurecloud.get_download_link_knowledge_base(file_name)
    if download_link is None:
        raise file_not_found_exec
    
    return {"download_link": download_link}

async def get_documents_list(session: Session):
    docs = session.query(KnowledgeBaseDocument)\
        .filter(KnowledgeBaseDocument.status != "del_failed").order_by(desc(KnowledgeBaseDocument.created_at)).all()
    
    # Clean up upload_failed docs after sending them
    session.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.status == "upload_failed"
                                                ).delete(synchronize_session='fetch')
    session.commit()
    
    files = []
    failed_files = []

    for doc in docs:
        if doc.status == "upload_failed":
            failed_files.append(FileInfo(filename=doc.document_name, content_type=doc.content_type, status="Failed to process file"))
        else:
            files.append(FileInfo(filename=doc.document_name, content_type=doc.content_type, status=doc.status))

    return DocumentsListResponse(files=files, failed_files=failed_files)

async def enqueue_file_deletions(file_names: List[str]):
    messages = []
    for batch in _chunk_data(file_names, size=256):
        message_body = json.dumps({"file_names": batch})
        messages.append(message_body)
    failed_messages = await azurecloud.send_messages_to_queue(settings.AZURE_STORAGE_KNOWLEDGEBASE_FILE_DELETE_QUEUE_NAME, messages)
    failed_files = []
    for msg, error in failed_messages:
        failed_file_names = json.loads(msg)["file_names"]
        failed_files.extend([FileInfo(filename=failed_file_name, error=error) for failed_file_name in failed_file_names])
    return DeleteDocumentsResponse(failed_files=failed_files)

async def get_azure_storage_token():
    token = azurecloud.get_container_sas_knowledge_base()
    return {"azure_storage_token": token}

def _chunk_data(list, size):
    for i in range(0, len(list), size):
        yield list[i:i + size]

def _is_document_in_db(filename, session: Session):
    doc = session.query(KnowledgeBaseDocument)\
        .filter(KnowledgeBaseDocument.document_name == filename).first()
    if doc:
        return True
    return False