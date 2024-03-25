import logging
from app.common.database import SessionLocal
from app.models.user import AdminConfig

OPENAI_MODEL_NAME = None
OPENAI_MODEL_TEMPERATURE = None
LLM_PROMPT = None
LLM_ROLE = None
GREETING_MESSAGE = None
DISCLAIMERS = None
GDRIVE_ENABLED = None
LOGO_LINK = None

def update_config():
    try:
        global OPENAI_MODEL_NAME
        global OPENAI_MODEL_TEMPERATURE
        global LLM_PROMPT
        global LLM_ROLE
        global GREETING_MESSAGE
        global DISCLAIMERS
        global GDRIVE_ENABLED
        global LOGO_LINK

        session = SessionLocal()
        admin_config = session.query(AdminConfig).first()
        if admin_config:
            OPENAI_MODEL_NAME = admin_config.llm_model_name
            OPENAI_MODEL_TEMPERATURE = admin_config.llm_temperature
            LLM_PROMPT = admin_config.llm_prompt
            LLM_ROLE = admin_config.llm_role
            GREETING_MESSAGE = admin_config.greeting_message
            DISCLAIMERS = admin_config.disclaimers
            GDRIVE_ENABLED = admin_config.gdrive_enabled
            LOGO_LINK = admin_config.logo_link
            logging.info(f"Admin config updated")
        else:
            logging.warn(f"No admin config in database | Inserting in database and using default admin config")
            admin_config = AdminConfig()
            OPENAI_MODEL_NAME = admin_config.llm_model_name = "gpt-4-turbo-preview"
            OPENAI_MODEL_TEMPERATURE = admin_config.llm_temperature = 0.4
            LLM_PROMPT = admin_config.llm_prompt = ""
            LLM_ROLE = admin_config.llm_role = "helpful assistant"
            GREETING_MESSAGE = admin_config.greeting_message = "Hi! I am Caira."
            DISCLAIMERS = admin_config.disclaimers = "Put your disclaimers"
            GDRIVE_ENABLED = admin_config.gdrive_enabled = False
            LOGO_LINK = admin_config.logo_link = "logo_link"
            session.add(admin_config)
            session.commit()

    except Exception as ex:
        logging.error(f"Exception occured while reading admin config from database | Using default admin config | Error: {ex}")
        OPENAI_MODEL_NAME = "gpt-4-turbo-preview"
        OPENAI_MODEL_TEMPERATURE = 0.4
        LLM_PROMPT = ""
        LLM_ROLE = "helpful assistant"
        GREETING_MESSAGE = "Hi! I am Caira."
        DISCLAIMERS = "Put your cisclaimers"
        GDRIVE_ENABLED = False
        LOGO_LINK = "logo_link"
    finally:
        session.close()
        
# setup admin config at startup
update_config()