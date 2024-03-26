from datetime import datetime, timedelta, timezone
import logging
from app.common.settings import get_settings
from azure.storage.blob.aio import ContainerClient as ContainerClientAsync
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, ContentSettings, ContainerClient

settings = get_settings()

consumer_container_client_async: ContainerClientAsync = ContainerClientAsync.from_connection_string(
    conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
    container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME)

consumer_container_client: ContainerClient = ContainerClient.from_connection_string(
    conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
    container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME)

kb_container_client_async: ContainerClientAsync = ContainerClientAsync.from_connection_string(
    conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
    container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME)

kb_container_client: ContainerClient = ContainerClient.from_connection_string(
    conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
    container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME)


async def upload_file_knowledge_base(file_content, file_name, content_type):
    blob_name = file_name
    try:
        await kb_container_client_async.upload_blob(name=blob_name, 
                                           data=file_content, 
                                           overwrite=True, 
                                           content_settings=ContentSettings(content_type=content_type),
                                           metadata={'uploaded_at': str(datetime.now(timezone.utc))})
        return {"filename": file_name, "status": "success"}
    except Exception as ex:
        logging.error(f"Error occured while uploading file to Azure Storage | Blob: {blob_name} | Error: {ex}")
        return {"filename": file_name, "status": "failed", "error": str(ex)}

async def upload_file(username, file_content, file_name, content_type):
    blob_name = f"{username}/{file_name}"
    try:
        await consumer_container_client_async.upload_blob(name=blob_name, 
                                           data=file_content, 
                                           overwrite=True, 
                                           content_settings=ContentSettings(content_type=content_type),
                                           metadata={'uploaded_at': str(datetime.now(timezone.utc)), 'user_id': username})
        return {"filename": file_name, "status": "success"}
    except Exception as ex:
        logging.error(f"Error occured while uploading file to Azure Storage | Blob: {blob_name} | Error: {ex}")
        return {"filename": file_name, "status": "failed", "error": str(ex)}

def blob_exists(blob_name):
    blob = consumer_container_client.get_blob_client(blob=blob_name)
    return blob.exists()

def blob_exists_knowledge_base(blob_name):
    blob = kb_container_client.get_blob_client(blob=blob_name)
    return blob.exists()

async def get_download_link_knowledge_base(file_name):
    blob_name=file_name
    if not blob_exists_knowledge_base(blob_name):
        return None
    
    blob_client = kb_container_client.get_blob_client(blob=blob_name)
    # Generate SAS token for the blob
    sas_token = generate_blob_sas(
        account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
        account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
        container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1) # Token valid for 1 hour
    )
    
    return f"{blob_client.url}?{sas_token}"

async def get_download_link(username, file_name):
    blob_name=f"{username}/{file_name}"
    if not blob_exists(blob_name):
        return None
    
    blob_client = consumer_container_client.get_blob_client(blob=blob_name)
    # Generate SAS token for the blob
    sas_token = generate_blob_sas(
        account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
        account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
        container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1) # Token valid for 1 hour
    )
    
    return f"{blob_client.url}?{sas_token}"

async def delete_file_knowledge_base(file_name):
    blob_name=file_name
    try:
        if blob_exists_knowledge_base(blob_name):
            blob_client = kb_container_client.get_blob_client(blob=blob_name)
            blob_client.delete_blob()
            return {"filename": file_name, "status": "success"}
        else:
            logging.error(f"Error occured while deleting file from Azure Storage | Blob: {blob_name} | Error: Blob not found in container. Skipping deletion.")
            return {"filename": file_name, "status": "failed", "error": f"Blob {blob_name} not found in container."}
    except Exception as ex:
            logging.error(f"Error occured while deleting file from Azure Storage | Blob: {blob_name} | Error: {ex}")
            return {"filename": file_name, "status": "failed", "error": str(ex)}

async def delete_file(username, file_name):
    blob_name=f"{username}/{file_name}"
    try:
        if blob_exists(blob_name):
            blob_client = consumer_container_client.get_blob_client(blob=blob_name)
            blob_client.delete_blob()
            return {"filename": file_name, "status": "success"}
        else:
            logging.error(f"Error occured while deleting file from Azure Storage | Blob: {blob_name} | Error: Blob not found in container. Skipping deletion.")
            return {"filename": file_name, "status": "failed", "error": f"Blob {blob_name} not found in container."}
    except Exception as ex:
            logging.error(f"Error occured while deleting file from Azure Storage | Blob: {blob_name} | Error: {ex}")
            return {"filename": file_name, "status": "failed", "error": str(ex)}