from pydantic import BaseModel
from datetime import datetime

class AdminConfigResponse(BaseModel):
    llm_model_name: str
    llm_temperature: float
    llm_prompt: str
    llm_role: str
    llm_streaming: str
    greeting_message: str
    disclaimers: str
    gdrive_enabled: bool
    logo_link: str
    updated_at: datetime
    
    class Config:
        orm_mode = True