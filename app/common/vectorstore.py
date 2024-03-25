from io import BytesIO, StringIO
import logging
import time
import pdfplumber
from pinecone import Pinecone, PodSpec
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from app.common.settings import get_settings
from app.common import openai
import os

settings = get_settings()

# Configure Pinecone
pinecone_instance = Pinecone(api_key=settings.PINECONE_API_KEY)
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

if settings.PINECONE_KNOWLEDGE_BASE_INDEX not in pinecone_instance.list_indexes().names():
    print(f'{settings.PINECONE_KNOWLEDGE_BASE_INDEX} Index does not exist, creating index...')
    pinecone_instance.create_index(name=settings.PINECONE_KNOWLEDGE_BASE_INDEX, spec=PodSpec(environment=settings.PINECONE_ENV), metric='cosine', dimension=1536)
    print(f"Updated pinecone indexes: {pinecone_instance.list_indexes()}")

if settings.PINECONE_CONSUMER_INDEX not in pinecone_instance.list_indexes().names():
    print(f'{settings.PINECONE_CONSUMER_INDEX} Index does not exist, creating index...')
    pinecone_instance.create_index(name=settings.PINECONE_CONSUMER_INDEX, spec=PodSpec(environment=settings.PINECONE_ENV), metric='cosine', dimension=1536)
    print(f"Updated pinecone indexes: {pinecone_instance.list_indexes()}")

def get_vector_store_instance(index_name, namespace):
    return PineconeVectorStore.from_existing_index(index_name, openai.openAIEmbeddings, namespace=namespace)

# For consumers only
async def delete_file(username, file_name):
    try:
        document_id = f"{username}/{file_name}"
        index = pinecone_instance.Index(settings.PINECONE_CONSUMER_INDEX)
        index.delete(
            namespace=username,
            filter={"document_id": {"$eq": document_id}}
        )
        return {"filename": file_name, "status": "success"}
    except Exception as ex:
        logging.error(f"Error occured while deleting file from Pinecone | File Name: {file_name} | Error: {ex}")
        return {"filename": file_name, "status": "failed", "error": str(ex)}

# For consumers only
async def upload_file(username, file_content, file_name, content_type):
    try:
        if content_type == 'application/pdf':
            with pdfplumber.open(BytesIO(file_content)) as filereader:
                file_content = ' '.join([page.extract_text() or "" for page in filereader.pages])
        else:
            stringio = StringIO(file_content.decode('utf-8'))
            file_content = stringio.read()

        file_to_upload = [Document(page_content=file_content, metadata={"document_id": f"{username}/{file_name}"})]
        vectorize_and_upload_documents(chunk_documents_by_tpm(file_to_upload), settings.PINECONE_CONSUMER_INDEX, username)
        return {"filename": file_name, "status": "success"}
   
    except Exception as ex:
        logging.error(f"Error occured while uploading file to Pinecone | File Name: {file_name} | Error: {ex}")
        return {"filename": file_name, "status": "failed", "error": str(ex)}

def chunk_documents_by_tpm(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=100, separators=[" ", ",", "\n"])
    chunked_docs = text_splitter.split_documents(documents)
    print(f'You have split your document into {len(chunked_docs)} smaller documents')
    
    # chunk documents to follow tokens per minute rate
    parentlist_listofdocs = []
    listofdocs = []
    tokens_per_listofdocs = 0
    total_tokens = 0

    for doc in chunked_docs:
        tokens_per_doc = num_tokens_from_string(doc.page_content + " " + str(doc.metadata), "cl100k_base")
        tokens_per_listofdocs += tokens_per_doc
        total_tokens += tokens_per_doc

        if tokens_per_listofdocs > 1000000:
            parentlist_listofdocs.append((listofdocs, tokens_per_listofdocs - tokens_per_doc))
            listofdocs = []
            tokens_per_listofdocs = tokens_per_doc

        listofdocs.append(doc)
    
    if len(listofdocs) > 0:
        parentlist_listofdocs.append((listofdocs, tokens_per_listofdocs))

    return parentlist_listofdocs

# vectorise and upload chunks
def vectorize_and_upload_documents(parentlist_listofdocs, index_name, namespace):
    vectorstore = get_vector_store_instance(index_name, namespace)
    listofdocs_counter = 1
    
    if len(parentlist_listofdocs) > 1:
        for listofdocs_per_min, tokens_per_minute in parentlist_listofdocs:
            vectorstore.add_documents(listofdocs_per_min, namespace=namespace)
            print(f"Documents Chunk Pushed To Vectorstore | {listofdocs_counter} out of {len(parentlist_listofdocs)} | " + 
                  f"Index Name: {index_name} | Namespace: {namespace} | Document Count: {len(listofdocs_per_min)} | Token Count: {tokens_per_minute}")
            
            if(listofdocs_counter < len(parentlist_listofdocs)):
                print("Sleeping for 1 minute | Tokens per minute exceeding 1000000")
                time.sleep(60)
            
            listofdocs_counter += 1
    else:
        listofdocs_per_min, tokens_per_minute = parentlist_listofdocs[0]
        vectorstore.add_documents(listofdocs_per_min, namespace=namespace)
        print(f"Documents Chunk Pushed To Vectorstore | Index Name: {index_name} | Namespace: {namespace} | " +
              f"Document Count: {len(listofdocs_per_min)} | Token Count: {tokens_per_minute}")

    print(f'All Documents Pushed To Vectorstore | Index Name: {index_name} | Namespace: {namespace}')

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens