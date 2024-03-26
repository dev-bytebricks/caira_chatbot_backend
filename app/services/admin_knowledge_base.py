import asyncio
from io import BytesIO, StringIO
import logging
from typing import List
from PyPDF2 import PdfReader
from fastapi import HTTPException, UploadFile, status
from app.models.user import KnowledgeBaseDocument
from app.schemas.responses.admin_knowledge_base import FileInfo, UploadDocumentsResponse, DeleteDocumentsResponse, DocumentsListResponse
from app.common import vectorstore, gdrive, azurecloud
from sqlalchemy.orm import Session

def _bytes_to_string(file_name, file_bytes, file_type):
    try:
        if file_type == 'application/pdf':
            pdf_reader = PdfReader(BytesIO(file_bytes))
            file_content = '\n'.join([page.extract_text() for i, page in enumerate(pdf_reader.pages)])
        else:
            stringio = StringIO(file_bytes.decode('utf-8'))
            file_content = stringio.read()
        return file_content
    except Exception as ex:
        logging.error(f"Error occured while converting bytes to string. File name: {file_name}, File Type: {file_type}, Error: {ex}")
        return None
    
async def _clone_content(original: BytesIO):
    content = original.getvalue()
    return content, content

def _is_document_in_db(filename, session: Session):
    doc = session.query(KnowledgeBaseDocument)\
        .filter(KnowledgeBaseDocument.document_name == filename).first()
    if doc:
        return True
    return False

async def _upload_file_to_services(file_content: BytesIO, file_name: str, file_type: str):
    file_content_clone1, file_content_clone2 = await _clone_content(file_content)
    
    # convert bytes to text before vectorizing
    file_content_str = _bytes_to_string(file_name, file_content_clone1, file_type)
    if file_content_str is None:
        return {"filename": file_name, "content_type": file_type, "status": "failed", "errors": [f"Error occured while converting bytes to string. File name: {file_name}, File Type: {file_type}"]}
    
    pinecone_upload_task = vectorstore.upload_file_knowledge_base(file_content_str, file_name)
    azure_upload_task = azurecloud.upload_file_knowledge_base(file_content_clone2, file_name, file_type)
    
    results = await asyncio.gather(azure_upload_task, pinecone_upload_task, return_exceptions=False)
    azure_result, pinecone_result = results
    
    # Initialize response structure
    response = {"filename": file_name, "content_type": file_type, "status": "success", "errors": []}
    
    # Check for errors and rollback accordingly
    if azure_result["status"] == "failed" or pinecone_result["status"] == "failed":
        
        if azure_result["status"] == "success":
            azure_file_delete_result = await azurecloud.delete_file_knowledge_base(file_name)
            if azure_file_delete_result["status"] == "failed":
                logging.error(f'Compensation deleting failed during upload rollback | File Name: {file_name} | Service: Azure | Error: {azure_file_delete_result["error"]}')
        
        if pinecone_result["status"] == "success":
            pinecone_file_delete_result = await vectorstore.delete_file_knowledge_base(file_name)
            if pinecone_file_delete_result["status"] == "failed":
                logging.error(f'Compensation deleting failed during upload rollback | File Name: {file_name} | Service: Pinecone | Error: {pinecone_file_delete_result["error"]}')    
        
        if azure_result["status"] == "failed":
            response["errors"].append(f'service: Azure, error: {azure_result["error"]}')
        
        if pinecone_result["status"] == "failed":
            response["errors"].append(f'service: Pinecone, error: {pinecone_result["error"]}')
        
        response["status"] = "failed"
    
    return response

async def _delete_file_from_services(filename: str):
    azure_delete_task = azurecloud.delete_file_knowledge_base(filename)
    pinecone_delete_task = vectorstore.delete_file_knowledge_base(filename)
    results = await asyncio.gather(azure_delete_task, pinecone_delete_task, return_exceptions=False)
    azure_result, pinecone_result = results
    
    # Initialize response structure
    response = {"filename": filename, "status": "success", "errors": []}
    
    # Check for errors
    if azure_result["status"] == "failed" or pinecone_result["status"] == "failed":

        if azure_result["status"] == "failed":
            response["errors"].append(f'service: Azure, error: {azure_result["error"]}')
            logging.error(f'Deleting failed | File Name: {filename} | Service: Azure | Error: {azure_result["error"]}')

        if pinecone_result["status"] == "failed":
            response["errors"].append(f'service: Pinecone, error: {pinecone_result["error"]}')
            logging.error(f'Deleting failed | File Name: {filename} | Service: Pinecone | Error: {pinecone_result["error"]}') 

        response["status"] = "failed"
    
    return response

async def upload_documents(files: List[UploadFile], session: Session):
    uploaded_files = []
    failed_files = []
    tasks = []

    # check if file is already uploaded
    for file in files:
        if _is_document_in_db(file.filename, session):
            failed_files.append(FileInfo(filename=file.filename, content_type=file.content_type, error="File with same name already exists"))
        else:
            tasks.append(_upload_file_to_services(BytesIO(await file.read()), file.filename, file.content_type))

    task_results = await asyncio.gather(*tasks)
    for task_result in task_results:
        filename = task_result["filename"]
        content_type = task_result["content_type"]
        if task_result["status"] == "success":
            try:
                session.add(KnowledgeBaseDocument(document_name=filename, content_type=content_type))
                session.commit()
                uploaded_files.append(FileInfo(filename=filename, content_type=content_type))
            except Exception as ex:
                logging.error(f"Uploading failed | File Name: {filename} | Database Error: {ex}")
                failed_files.append(FileInfo(filename=filename, content_type=content_type, error=f"Database Error: {ex}"))
        else:
            failed_files.append(FileInfo(filename=filename, content_type=content_type, error=" | ".join(task_result["errors"])))

    return UploadDocumentsResponse(uploaded_files=uploaded_files, failed_files=failed_files)

async def upload_documents_gdrivelink(gdrivelink, session):
    # download files from google drive
    downloaded_files = await gdrive.get_files_from_link(gdrivelink)

    uploaded_files = []
    failed_files = []
    tasks = []

    # check if file is already uploaded
    for file in downloaded_files:
        if _is_document_in_db(file.get("file_name"), session):
            failed_files.append(FileInfo(filename=file.get("file_name"), content_type=file.get("file_type"), error="File with same name already exists"))
        else:
            tasks.append(_upload_file_to_services(file.get("file_bytes"), file.get("file_name"), file.get("file_type")))

    task_results = await asyncio.gather(*tasks)
    for task_result in task_results:
        filename = task_result["filename"]
        content_type = task_result["content_type"]
        if task_result["status"] == "success":
            try:
                session.add(KnowledgeBaseDocument(document_name=filename, content_type=content_type))
                session.commit()
                uploaded_files.append(FileInfo(filename=filename, content_type=content_type))
            except Exception as ex:
                logging.error(f"Uploading failed | File Name: {filename} | Database Error: {ex}")
                failed_files.append(FileInfo(filename=filename, content_type=content_type, error=f"Database Error: {ex}"))
        else:
            failed_files.append(FileInfo(filename=filename, content_type=content_type, error=" | ".join(task_result["errors"])))

    return UploadDocumentsResponse(uploaded_files=uploaded_files, failed_files=failed_files)

async def get_download_link(file_name, session: Session):
    file_not_found_exec = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not _is_document_in_db(file_name, session):
        raise file_not_found_exec

    download_link = await azurecloud.get_download_link_knowledge_base(file_name)
    if download_link is None:
        raise file_not_found_exec
    
    return {"download_link": download_link}

async def delete_documents(file_names, session: Session):
    deleted_files = []
    failed_files = []
    tasks = []

    # check if file is already deleted
    for file_name in file_names:
        if not _is_document_in_db(file_name, session):
            failed_files.append(FileInfo(filename=file_name, error="File does not exists"))
        else:
            tasks.append(_delete_file_from_services(file_name))

    task_results = await asyncio.gather(*tasks)
    
    for task_result in task_results:
        filename = task_result["filename"]
        try:
            if task_result["status"] == "failed":
                logging.error(f'Unable delete file from services | File Name: {filename} | Error: {" | ".join(task_result["errors"])}')
            session.query(KnowledgeBaseDocument)\
                .filter(KnowledgeBaseDocument.document_name == filename).delete(synchronize_session='fetch')
            session.commit()
            deleted_files.append(FileInfo(filename=filename))
        except Exception as ex:
            logging.error(f"Deleting failed | File Name: {filename} | Database Error: {ex}")
            failed_files.append(FileInfo(filename=filename, error=f"Database Error: {ex}"))
    
    return DeleteDocumentsResponse(deleted_files=deleted_files, failed_files=failed_files)

async def get_documents_list(session: Session):
    docs = session.query(KnowledgeBaseDocument).all()
    return DocumentsListResponse(files=[FileInfo(filename=doc.document_name, content_type=doc.content_type) for doc in docs])

