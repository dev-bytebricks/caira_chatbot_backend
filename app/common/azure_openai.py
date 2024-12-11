# import logging
# from app.common.settings import get_settings
# from app.common.adminconfig import AdminConfig
# from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings


# settings = get_settings()
# logger = logging.getLogger(__name__)

# class AzureOpenAIManager:

#     EMBEDDINGS = AzureOpenAIEmbeddings(
#             openai_api_version=settings.AZURE_OPENAI_API_VERSION,
#             azure_deployment=settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME)
    
#     CHAT_SECONDARY = AzureChatOpenAI(
#             openai_api_version=settings.AZURE_OPENAI_API_VERSION,
#             azure_deployment=settings.AZURE_OPENAI_CHAT_SECONDARY_DEPLOYMENT_NAME,
#             temperature=0)
    
#     CHAT_PRIMARY: AzureChatOpenAI

#     @classmethod
#     def update_primary_chat_instance(cls):
#         cls.CHAT_PRIMARY = AzureChatOpenAI(
#             openai_api_version=settings.AZURE_OPENAI_API_VERSION,
#             azure_deployment=settings.AZURE_OPENAI_CHAT_PRIMARY_DEPLOYMENT_NAME,
#             temperature=AdminConfig.OPENAI_MODEL_TEMPERATURE,
#             streaming=AdminConfig.LLM_STREAMING
#             )
        
#         logger.info(f"Azure OpenAI primary chat client initialised")

# # setup openAIChat at startup
# AzureOpenAIManager.update_primary_chat_instance()
