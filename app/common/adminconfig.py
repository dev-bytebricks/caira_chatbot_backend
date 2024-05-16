import logging
from app.common.database import SessionLocal
from app.models.user import AdminConfig as AdminConfigModel

logger = logging.getLogger(__name__)

class AdminConfig:
    OPENAI_MODEL_NAME: str
    OPENAI_MODEL_TEMPERATURE: int
    LLM_STREAMING: bool
    LLM_PROMPT : str
    LLM_ROLE: str
    GREETING_MESSAGE: str
    DISCLAIMERS: str
    GDRIVE_ENABLED: str
    LOGO_LINK: str

    @classmethod
    def update_config(cls):
        try:
            session = SessionLocal()
            admin_config = session.query(AdminConfigModel).first()
            if admin_config:
                cls.OPENAI_MODEL_NAME = admin_config.llm_model_name
                cls.OPENAI_MODEL_TEMPERATURE = admin_config.llm_temperature
                cls.LLM_STREAMING = admin_config.llm_streaming
                cls.LLM_PROMPT = admin_config.llm_prompt
                cls.LLM_ROLE = admin_config.llm_role
                cls.GREETING_MESSAGE = admin_config.greeting_message
                cls.DISCLAIMERS = admin_config.disclaimers
                cls.GDRIVE_ENABLED = admin_config.gdrive_enabled
                cls.LOGO_LINK = admin_config.logo_link
                logger.info(f"Admin config loaded from database")
            else:
                logger.warn(f"No admin config in database | Inserting in database and using default admin config")
                admin_config = AdminConfigModel()
                cls.OPENAI_MODEL_NAME = admin_config.llm_model_name = "gpt-4-turbo-preview"
                cls.OPENAI_MODEL_TEMPERATURE = admin_config.llm_temperature = 0.4
                cls.LLM_STREAMING = True
                cls.LLM_PROMPT = admin_config.llm_prompt = ""
                cls.LLM_ROLE = admin_config.llm_role = "helpful assistant"
                cls.GREETING_MESSAGE = admin_config.greeting_message = "Hi! I am Caira."
                cls.DISCLAIMERS = admin_config.disclaimers = "Put your disclaimers"
                cls.GDRIVE_ENABLED = admin_config.gdrive_enabled = False
                cls.LOGO_LINK = admin_config.logo_link = "logo_link"
                session.add(admin_config)
                session.commit()

        except Exception as ex:
            logger.exception(f"Exception occured while reading admin config from database | Using default admin config | Error: {ex}")
            cls.OPENAI_MODEL_NAME = "gpt-4-turbo-preview"
            cls.OPENAI_MODEL_TEMPERATURE = 0.4
            cls.LLM_STREAMING = True
            cls.LLM_PROMPT = ""
            cls.LLM_ROLE = "helpful assistant"
            cls.GREETING_MESSAGE = "Hi! I am Caira."
            cls.DISCLAIMERS = "Put your cisclaimers"
            cls.GDRIVE_ENABLED = False
            cls.LOGO_LINK = "logo_link"
        finally:
            session.close()
        
# setup admin config at startup
AdminConfig.update_config()