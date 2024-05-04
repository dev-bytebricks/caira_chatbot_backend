import logging
from app.common.settings import get_settings
from app.common.adminconfig import AdminConfig
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

settings = get_settings()
logger = logging.getLogger(__name__)

class OpenAIManager:

    OPENAI_EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
    OPENAI_CHAT_SECONDARY = ChatOpenAI(
            model="gpt-3.5-turbo", 
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0
            )
    OPENAI_CHAT_PRIMARY: ChatOpenAI

    @classmethod
    def update_openai_chat_instance(cls):
        cls.OPENAI_CHAT_PRIMARY = ChatOpenAI(
            model=AdminConfig.OPENAI_MODEL_NAME, 
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE,
            streaming= AdminConfig.LLM_STREAMING
            )
        logger.info(f"OpenAI chat client initialised")

# setup openAIChat at startup
OpenAIManager.update_openai_chat_instance()

