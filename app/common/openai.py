from app.common.settings import get_settings
from app.common.adminconfig import OPENAI_MODEL_NAME, OPENAI_MODEL_TEMPERATURE
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

settings = get_settings()

openAIEmbeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=settings.OPENAI_API_KEY)
openAIChat = None

def update_openai_chat_instance():
    global openAIChat
    openAIChat = ChatOpenAI(
        model=OPENAI_MODEL_NAME, 
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=OPENAI_MODEL_TEMPERATURE
        )
        
# setup openAIChat at startup
update_openai_chat_instance()