import logging
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from app.common.settings import get_settings
from app.common.azure_openai import AzureOpenAIManager
import os

logger = logging.getLogger(__name__)

settings = get_settings()

# Configure Pinecone
pinecone_instance = Pinecone(api_key=settings.PINECONE_API_KEY)
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY

def get_vector_store_instance(index_name, namespace):
    return PineconeVectorStore.from_existing_index(index_name, AzureOpenAIManager.EMBEDDINGS, namespace=namespace)