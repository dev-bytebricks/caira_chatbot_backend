from typing import Optional
from pydantic import BaseModel

class UpdateAdminConfigRequest(BaseModel):
    llm_model_name: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_prompt: Optional[str] = None
    llm_role: Optional[str] = None
    llm_streaming: Optional[bool] = None
    greeting_message: Optional[str] = None
    disclaimers: Optional[str] = None
    gdrive_enabled: Optional[bool] = None
    logo_link: Optional[str] = None