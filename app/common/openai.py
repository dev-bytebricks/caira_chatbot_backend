import logging
from app.common.settings import get_settings
from app.common.adminconfig import AdminConfig
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

settings = get_settings()
logger = logging.getLogger(__name__)

class OpenAIManager:

    OPENAI_EMBEDDINGS = AzureOpenAIEmbeddings(
            azure_endpoint=settings.JAVELIN_API_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            api_key=settings.AZURE_OPENAI_API_KEY,
            model_kwargs={
            "extra_headers": {
                "x-api-key": settings.JAVELIN_API_KEY, 
                "x-javelin-route": settings.JAVELIN_EMBEDDINGS_ROUTE
                }
            })
    
    OPENAI_CHAT_SECONDARY = AzureChatOpenAI(
            azure_endpoint=settings.JAVELIN_API_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            api_key=settings.AZURE_OPENAI_API_KEY,
            model_kwargs={
            "extra_headers": {
                "x-api-key": settings.JAVELIN_API_KEY, 
                "x-javelin-route": settings.JAVELIN_CHAT_SECONDARY_ROUTE
                }
            },
            temperature=0)
    
    OPENAI_CHAT_PRIMARY: AzureChatOpenAI

    @classmethod
    def update_openai_chat_instance(cls):
        cls.OPENAI_CHAT_PRIMARY = AzureChatOpenAI(
            azure_endpoint=settings.JAVELIN_API_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            api_key=settings.AZURE_OPENAI_API_KEY,
            model_kwargs={
            "extra_headers": {
                "x-api-key": settings.JAVELIN_API_KEY, 
                "x-javelin-route": settings.JAVELIN_CHAT_PRIMARY_ROUTE
                }
            },
            temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE,
            streaming=AdminConfig.LLM_STREAMING
            )
        
        logger.info(f"Javelin primary chat client initialised")

# setup openAIChat at startup
OpenAIManager.update_openai_chat_instance()
