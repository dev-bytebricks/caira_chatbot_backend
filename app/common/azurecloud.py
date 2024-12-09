import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
from typing import List
from app.common.settings import get_settings
from azure.storage.blob import generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions, ContainerClient
from azure.storage.queue.aio import QueueServiceClient, QueueClient
from azure.storage.queue import TextBase64EncodePolicy, TextBase64DecodePolicy
from azure.messaging.webpubsubservice.aio import WebPubSubServiceClient
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)

settings = get_settings()

WEB_PUBSUB_ADMIN_GROUP = "admin"

# web_pubsub_client: WebPubSubServiceClient = WebPubSubServiceClient(
#     endpoint=settings.AZURE_WEB_PUBSUB_ENDPOINT, 
#     credential=AzureKeyCredential(settings.AZURE_WEB_PUBSUB_KEY), 
#     hub="notification")

# consumer_container_client: ContainerClient = ContainerClient.from_connection_string(
#     conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
#     container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME)

# kb_container_client: ContainerClient = ContainerClient.from_connection_string(
#     conn_str=settings.AZURE_STORAGE_CONNECTION_STRING, 
#     container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME)

# queue_service_client: QueueServiceClient = QueueServiceClient.from_connection_string(
#     conn_str=settings.AZURE_STORAGE_CONNECTION_STRING
# )

# async def notify_all_app_events(event_type):
#     await web_pubsub_client.send_to_all(message=json.dumps({"event_type": event_type}))

# async def notify_user_file_events(user_id, file_name, status, event_type):
#     await web_pubsub_client.send_to_user(user_id=user_id, 
#                                                message=json.dumps({"file_name": file_name, 
#                                                                    "status": status,
#                                                                    "event_type": event_type}))

# async def notify_kb_file_events(file_name, status, event_type):
#     await web_pubsub_client.send_to_group(group=WEB_PUBSUB_ADMIN_GROUP, 
#                                                 message=json.dumps({"file_name": file_name, 
#                                                                     "status": status,
#                                                                     "event_type": event_type}))

# async def get_pubsub_client_token_admin(username):
#     response = await web_pubsub_client.get_client_access_token(user_id=username, roles=[f"webpubsub.joinLeaveGroup.{WEB_PUBSUB_ADMIN_GROUP}"])
#     return response["token"]

# async def get_pubsub_client_token(username):
#     response = await web_pubsub_client.get_client_access_token(user_id=username)
#     return response["token"]

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
        container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME,
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
        container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1) # Token valid for 1 hour
    )

    return f"{blob_client.url}?{sas_token}"

# def get_container_sas():
#     sas_token = generate_container_sas(
#         account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
#         account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
#         container_name=settings.AZURE_STORAGE_CONSUMER_CONTAINER_NAME,
#         permission=ContainerSasPermissions(write=True, list=True),
#         expiry=datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
#     )
#     return sas_token

# def get_container_sas_knowledge_base():
#     sas_token = generate_container_sas(
#         account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
#         account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
#         container_name=settings.AZURE_STORAGE_KNOWLEDGE_BASE_CONTAINER_NAME,
#         permission=ContainerSasPermissions(write=True, list=True),
#         expiry=datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
#     )
#     return sas_token

# async def send_messages_to_queue(queue_name: str, messages: List[str]):
#     queue_client: QueueClient = queue_service_client.get_queue_client(
#         queue_name,
#         message_encode_policy = TextBase64EncodePolicy(),
#         message_decode_policy = TextBase64DecodePolicy()
#         )
#     tasks = []

#     for message in messages:
#         # Create a task for each message, handling errors individually
#         task = _send_message_to_queue_safely(queue_client, message)
#         tasks.append(task)

#     # Wait for all tasks to complete
#     results = await asyncio.gather(*tasks, return_exceptions=True)
    
#     # Analyze results
#     failed_messages = []

#     for message, result in zip(messages, results):
#         if result is not None:
#             failed_messages.append((message, str(result)))
    
#     return failed_messages

# async def _send_message_to_queue_safely(queue_client: QueueClient, message: str):
#     try:
#         await queue_client.send_message(message)
#         return None
#     except Exception as ex:
#         return ex