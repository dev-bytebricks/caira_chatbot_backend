import logging
from app.common.settings import get_settings
from app.common.adminconfig import AdminConfig
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

settings = get_settings()
logger = logging.getLogger(__name__)

class OpenAIManager:

    OPENAI_EMBEDDINGS = AzureOpenAIEmbeddings(
        azure_deployment=settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME,
        openai_api_version=settings.AZURE_OPENAI_API_VERSION)
    
    OPENAI_CHAT_SECONDARY = AzureChatOpenAI(
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_CHAT_SECONDARY_DEPLOYMENT_NAME,
            temperature=0)
    
    OPENAI_CHAT_PRIMARY: AzureChatOpenAI

    @classmethod
    def update_openai_chat_instance(cls):
        cls.OPENAI_CHAT_PRIMARY = AzureChatOpenAI(
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_CHAT_PRIMARY_DEPLOYMENT_NAME,
            temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE,
            streaming=AdminConfig.LLM_STREAMING
            )
        logger.info(f"OpenAI chat client initialised")

# setup openAIChat at startup
OpenAIManager.update_openai_chat_instance()

