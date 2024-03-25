from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UpdateAdminConfigRequest(BaseModel):
    llm_model_name: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_prompt: Optional[str] = None
    llm_role: Optional[str] = None
    greeting_message: Optional[str] = None
    disclaimers: Optional[str] = None
    gdrive_enabled: Optional[bool] = None
    logo_link: Optional[str] = None
    updated_at: Optional[datetime] = None