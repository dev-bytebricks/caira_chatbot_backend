import logging
from app.common.settings import get_settings
from app.common.adminconfig import AdminConfig
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

settings = get_settings()
logger = logging.getLogger(__name__)

class OpenAIManager:

    OPENAI_EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=settings.OPENAI_API_KEY)
    OPENAI_CHAT: ChatOpenAI

    @classmethod
    def update_openai_chat_instance(cls):
        cls.OPENAI_CHAT = ChatOpenAI(
            model=AdminConfig.OPENAI_MODEL_NAME, 
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE
            )
        logger.info(f"OpenAI chat client updated")

# setup openAIChat at startup
OpenAIManager.update_openai_chat_instance()

