import logging
from app.common.settings import get_settings
from app.common.adminconfig import AdminConfig
from langchain_openai import ChatOpenAI

settings = get_settings()
logger = logging.getLogger(__name__)

class OpenAIManager:
    
    CHAT_SECONDARY = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_CHAT_SECONDARY_MODEL_NAME,
        temperature=0)
    
    CHAT_PRIMARY: ChatOpenAI

    @classmethod
    def update_primary_chat_instance(cls):
        cls.CHAT_PRIMARY = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_CHAT_PRIMARY_MODEL_NAME,
            temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE,
            streaming=AdminConfig.LLM_STREAMING
            )
        
        logger.info(f"OpenAI primary chat client initialised")

# setup openAIChat at startup
OpenAIManager.update_primary_chat_instance()
