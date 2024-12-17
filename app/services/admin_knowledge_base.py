import json
import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy import case, desc
from app.common.settings import get_settings
from app.models.user import KnowledgeBaseDocument
from app.schemas.responses.admin_knowledge_base import FileInfo, DeleteDocumentsResponse, DocumentsListResponse, ValidateDocumentsResponse, FileExists #, GdriveUploadResponse
from app.common import gdrive, azurecloud
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.responses import FileResponse
from app.common.text_extractor import extract_text
from app.common.upload_file_vector_store import PINECONE_KB_INDEX_CLIENT,delete_file,upload_file,get_kb_download_file_link
from app.common import database_helper

settings = get_settings()

logger = logging.getLogger(__name__)

async def manage_kb_upload_file(files, session):
    base_directory = Path('/app/static/') / 'knowledge_base'
    # Create the directory for the user if it does not exist
    base_directory.mkdir(parents=True, exist_ok=True)
    for file in files:
        # Construct the file path
        file_path = base_directory / file.filename
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
            print(f"File '{file.filename}' saved at '{file_path}'.")
            # Extract text from the file
        file_type = file.content_type
        extracted_text = extract_text(file.filename, contents, file_type)
        kb_doc_db = database_helper.get_file_from_kb_db(file.filename)
        if kb_doc_db:
            if kb_doc_db.status == "Completed":
                try:
                    # Delete pre-existing vectors from Pinecone with same name (consumer vector id pattern -> user_name:file_name:chunk_num)
                    await delete_file(f"{file.filename}:", PINECONE_KB_INDEX_CLIENT)
                    database_helper.delete_kb_file_entry(file.filename)
                except Exception as e:
                    logger.error(f"Error during deleting from pinecone and database: {e}")
                    await delete_file(f"{file.filename}:", PINECONE_KB_INDEX_CLIENT)
                    database_helper.delete_kb_file_entry(file.filename)
                    logger.error(f"Deleted succefully from pinecone and database and created fresh entry")
                # file_name_formated = f'{file.filename}::'
                # await delete_file(file_name_formated, PINECONE_KB_INDEX_CLIENT)
        try:
            database_helper.create_kb_file_entry(file.filename, "Completed", file_type)
            await upload_file(f"{file.filename}:", extracted_text, PINECONE_KB_INDEX_CLIENT, settings.EMBEDDINGS_MODEL_NAME)
            logger.info(f"func_process_uploaded_files_kb --> Finished | File Name: {file.filename}")
        except Exception as e:
            logger.error(f"Error during vectorization and chunking: {e}")
            database_helper.update_kb_file_entry(file.filename, "Failed")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload OpenAI quata complted. Please recharge your Openai account."
            )


# async def enqueue_gdrive_upload(gdrivelink, session: Session):
#     files_info = await gdrive.get_files_info_from_link(gdrivelink)

#     if len(files_info) > 200:
#          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max 200 files are allowed per Google Drive link")

#     unique_files = {}
#     for file_info in files_info:
#         file_name = file_info["name"]
#         # Add file info to the dictionary if the name has not been added yet
#         if file_name not in unique_files:
#             unique_files[file_name] = file_info

#     # Now unique_files contains only one entry per file name
#     files_info = list(unique_files.values()) 

#     failed_files = []
#     files_to_enqueue = []

#     # check if file is already uploaded
#     for file_info in files_info:
#         file_name = file_info["name"]
#         file_type = file_info["mimeType"]
#         if file_type == "application/vnd.google-apps.document":
#             file_name += ".pdf"
        
#         # check if file exists in database
#         doc = session.query(KnowledgeBaseDocument)\
#             .filter(KnowledgeBaseDocument.document_name == file_name,
#                     KnowledgeBaseDocument.status != "del_failed").first()

#         if doc:
#             # add logging for multiple statuses here (for completed status show same file exists but for other statuses show file upload is in progress)
#             failed_files.append(FileInfo(filename=file_name, error="File with same name already exists"))
#         else:
#             files_to_enqueue.append(file_info)

#     if len(files_to_enqueue) == 0:
#         return GdriveUploadResponse(queued_files=[], failed_files=failed_files)

#     queued_files = []
#     # create file entry with transferring status for files in db
#     for file_to_enqueue in files_to_enqueue:
#         file_name = file_to_enqueue["name"]
#         file_type = file_to_enqueue["mimeType"]
#         if file_type == "application/vnd.google-apps.document":
#             file_name += ".pdf"
#         session.add(KnowledgeBaseDocument(document_name=file_name, content_type=file_type, status="Queued For Google Drive Transfer"))
#         session.commit()
#         # assume that file has been queued and handle failure after actual queuing
#         queued_files.append(FileInfo(filename=file_name, status="Queued For Google Drive Transfer"))

#     messages_to_enqueue = []
#     for batch in _chunk_data(files_to_enqueue, size=200):
#         message_body = json.dumps({"files_info": batch})
#         messages_to_enqueue.append(message_body)

#     failed_messages = await azurecloud.send_messages_to_queue(settings.AZURE_STORAGE_KNOWLEDGEBASE_GDRIVE_UPLOAD_QUEUE_NAME, messages_to_enqueue)

#     # handle failed to enqueue files
#     for msg, error in failed_messages:
#         failed_files_info = json.loads(msg)["files_info"]
#         for failed_file_info in failed_files_info:
#             file_name = failed_file_info["name"]
#             file_type = failed_file_info["mimeType"]
#             if file_type == "application/vnd.google-apps.document":
#                 file_name += ".pdf"
#             # update failed files and queued files list
#             failed_files.append(FileInfo(filename=file_name, error=error))
#             queued_files = [file for file in queued_files if not (file.filename == file_name and file.status == "Queued For Google Drive Transfer")]
#             # remove file entry from db
#             session.query(KnowledgeBaseDocument)\
#                 .filter(
#                     KnowledgeBaseDocument.document_name == file_name,
#                     KnowledgeBaseDocument.status == "Queued For Google Drive Transfer"
#                     ).delete(synchronize_session='fetch')
#             session.commit()

#     return GdriveUploadResponse(queued_files=queued_files, failed_files=failed_files)

async def get_download_link(file_name, session: Session):
    file_not_found_exec = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # check if file exists in database with completed status
    doc = session.query(KnowledgeBaseDocument)\
        .filter(KnowledgeBaseDocument.document_name == file_name,
                KnowledgeBaseDocument.status == "Completed").first()

    if not doc:
        raise file_not_found_exec

    file_path = await get_kb_download_file_link(file_name)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found."
        )
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=file_name
    )

async def get_documents_list(session: Session):
    uploaded_user_docs = session.query(
        KnowledgeBaseDocument.document_name,
        KnowledgeBaseDocument.content_type, 
        KnowledgeBaseDocument.status)\
        .filter(
            KnowledgeBaseDocument.status == "Completed"
            ).order_by(desc(KnowledgeBaseDocument.created_at)).all()

    failed_user_docs = session.query(
        KnowledgeBaseDocument.document_name,
        KnowledgeBaseDocument.content_type, 
        case((KnowledgeBaseDocument.status == 'upload_failed', 'Upload Failed'), else_=KnowledgeBaseDocument.status).label("status"))\
        .filter(
            KnowledgeBaseDocument.status == "upload_failed"
            ).order_by(desc(KnowledgeBaseDocument.created_at)).all()

    processing_user_docs = session.query(
        KnowledgeBaseDocument.document_name,
        KnowledgeBaseDocument.content_type, 
        case((KnowledgeBaseDocument.status == 'to_delete', 'Deleting'), else_=KnowledgeBaseDocument.status).label("status"))\
        .filter(
            KnowledgeBaseDocument.status != "upload_failed",
            KnowledgeBaseDocument.status != "Completed",
            KnowledgeBaseDocument.status != "del_failed"
            ).order_by(desc(KnowledgeBaseDocument.created_at)).all()

    # Clean up upload_failed docs after sending them
    session.query(KnowledgeBaseDocument)\
        .filter(
            KnowledgeBaseDocument.status == "upload_failed"
            ).delete(synchronize_session='fetch')
    session.commit()

    # Map query results to FileInfo
    uploaded_files = [FileInfo(filename=doc[0], content_type=doc[1], status=doc[2]) for doc in uploaded_user_docs]
    failed_files = [FileInfo(filename=doc[0], content_type=doc[1], status=doc[2]) for doc in failed_user_docs]
    processing_files = [FileInfo(filename=doc[0], content_type=doc[1], status=doc[2]) for doc in processing_user_docs]
            
    return DocumentsListResponse(uploaded_files=uploaded_files, processing_files=processing_files, failed_files=failed_files)

async def delete_files_from_kb_db(file_names, session: Session):
    failed_files = []

    for file_name in file_names:
        # check if file exists in database with completed status
        doc = session.query(KnowledgeBaseDocument)\
            .filter(KnowledgeBaseDocument.document_name == file_name).first()
        if doc:
            session.delete(doc)
        else:
            failed_files.append(FileInfo(filename=file_name, error="File does not exists"))
        file_name_formated = f'{file_name}::chunk'
        await delete_file(file_name_formated, PINECONE_KB_INDEX_CLIENT)
        session.commit()
        return DeleteDocumentsResponse(failed_files=failed_files)

    return DeleteDocumentsResponse(failed_files=failed_files)

# async def get_azure_storage_token():
#     token = azurecloud.get_container_sas_knowledge_base()
#     return {"azure_storage_token": token}

def _chunk_data(list, size):
    for i in range(0, len(list), size):
        yield list[i:i + size]

async def validate_filenames(file_names: List[str], session: Session):
    if len(file_names) == 0:
        return ValidateDocumentsResponse(files=[])
    
    existing_files = session.query(KnowledgeBaseDocument)\
        .filter(KnowledgeBaseDocument.document_name.in_(file_names), 
                KnowledgeBaseDocument.status != "del_failed")\
        .all()
    
    existing_file_set = {doc.document_name for doc in existing_files}

    return ValidateDocumentsResponse(files=[FileExists(filename=file_name, exists=file_name in existing_file_set) for file_name in file_names])