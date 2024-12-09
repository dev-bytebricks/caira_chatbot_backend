from itertools import islice
from openai import AsyncAzureOpenAI, RateLimitError
import logging, tiktoken, backoff
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from pinecone.grpc import GRPCIndex
import os
from langchain_openai import OpenAIEmbeddings
from app.common import settings
from pinecone import Pinecone


logger = logging.getLogger(__name__)

# Declare global variables
SETTINGS = None
AZURE_OPENAI_CLIENT = None
PINECONE_CLIENT = None
PINECONE_KB_INDEX_CLIENT = None
PINECONE_CONUMER_INDEX_CLIENT = None
AZURE_CONSUMER_CONTAINER_CLIENT = None
AZURE_KB_CONTAINER_CLIENT = None

def _setup_dependencies():
    global SETTINGS, AZURE_OPENAI_CLIENT, PINECONE_CLIENT, PINECONE_KB_INDEX_CLIENT, PINECONE_CONUMER_INDEX_CLIENT, AZURE_CONSUMER_CONTAINER_CLIENT, AZURE_KB_CONTAINER_CLIENT

    if SETTINGS:
        return
    # Get App Settings
    SETTINGS = settings.Settings()
    # Initialise Pinecone
    PINECONE_CLIENT = Pinecone(api_key=SETTINGS.PINECONE_API_KEY)
    PINECONE_KB_INDEX_CLIENT = PINECONE_CLIENT.Index(name=SETTINGS.PINECONE_KNOWLEDGE_BASE_INDEX)
    PINECONE_CONUMER_INDEX_CLIENT = PINECONE_CLIENT.Index(name=SETTINGS.PINECONE_CONSUMER_INDEX)
    
    logger.info("Pinecone client initialised")

_setup_dependencies()
@backoff.on_exception(backoff.expo, Exception, max_time=10, jitter=backoff.random_jitter, logger=logger)
async def delete_file(file_name: str, pc_index: Pinecone.Index):
    """For consumers, file_name should always follow the pattern -> user_name:file_name:"""
    try:
        logger.warn(f"Trying to delete file from Pinecone | File Name: {file_name} | Index: {pc_index}")
        to_delete = []
        all_ids = pc_index.list(prefix=file_name)
        
        for ids in all_ids:
            to_delete.extend(ids)
        print(f'ids to delete from pinecone {to_delete}')
        if len(to_delete) > 0:
            for batch in _chunk_into_batches(to_delete, 1000):
                res = pc_index.delete(ids=batch)
                logger.info(f"Deleted file chunks from Pinecone | Vector Ids: {batch} | Index: {pc_index} | Response: {res}")
    except Exception as ex:
        raise Exception(f"Unable to delete file from Pinecone | File Name: {file_name} | Index: {pc_index} | Error: {ex}")

async def upload_file(file_name: str, file_content: str, pc_index: Pinecone.Index, embeddings_model_name: str):
    """For consumers, file_name should always follow the pattern -> user_name:file_name"""
    # try:
    logger.info(f"Uploading file to Pinecone | File Name: {file_name} | Index: {pc_index}")
    # Chunk file content into chunks of 4000 characters
    chunks = _chunk_text(file_content)
    logger.info(f"File content split into {len(chunks)} chunks | File Name: {file_name} | Total Tokens: {_num_tokens_from_string(file_content)}")
    
    # Initialise list for Pinecone vector insertion
    vectors_to_insert = []
    # Keep track of the overall chunk_num across all chunks
    chunk_num = 1
    for batch in _chunk_into_batches(chunks, 20):
        # Vectorise the batch using OpenAI embeddings (using batching to respect tokens per request limit)
        response = await _get_embeddings(embeddings_model_name, batch)
        # Process each chunk in the batch
        for vector_data, text in zip(response, batch):
            vector_id = f"{file_name}:chunk{chunk_num}"
            vector = vector_data
            vectors_to_insert.append((vector_id, vector, {"file_name": file_name, "chunk_num": chunk_num, "text": text}))
            # Increment the chunk_num for each processed chunk
            chunk_num += 1

    # Insert vectors in batches to Pinecone
    for batch in _chunk_into_batches(vectors_to_insert, 100):
        print(f'diamnetion in batch during upsert {len(batch[0])}')
        response = _upsert_to_pinecone(pc_index=pc_index, vectors=batch)
        logger.info(f"File uploaded successfully to Pinecone | File Name: {file_name} | Index: {pc_index} | Upsert Response: {response}")
    # except Exception as ex:
    #     raise Exception(f"Unable to upload file on Pinecone | File Name: {file_name} | Index: {pc_index} | Error: {ex}")

@backoff.on_exception(backoff.expo, Exception, max_time=10, jitter=backoff.random_jitter, logger=logger)
def _upsert_to_pinecone(pc_index: Pinecone.Index, vectors: List[tuple]):
    return pc_index.upsert(vectors=vectors)

@backoff.on_exception(backoff.expo, RateLimitError, max_time=90, jitter=backoff.random_jitter, logger=logger)
async def _get_embeddings(embeddings_model_name: str, text_list: List[str]):
    embeddings_model  = OpenAIEmbeddings(model=embeddings_model_name)
    return embeddings_model.embed_documents(text_list)

def _chunk_into_batches(seq: List[str], size: int):
    it = iter(seq)
    while batch := list(islice(it, size)):
        yield batch

def _chunk_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=100, separators=[" ", ",", "\n"])
    chunked_texts = text_splitter.split_text(text)
    return chunked_texts

def _num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

async def get_download_file_link(username: str, file_name: str):
    base_path = "static"
    file_path = os.path.join(base_path, str(username), file_name)
    if not os.path.exists(file_path):
        return None  
    return file_path



async def get_kb_download_file_link( file_name: str):
    base_path = "static"
    file_path = os.path.join(base_path, 'knowledge_base', file_name)
    if not os.path.exists(file_path):
        return None  
    return file_path
