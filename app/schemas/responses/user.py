from typing import Union
from datetime import datetime
from pydantic import EmailStr, BaseModel
from app.models.user import Role
from app.schemas.responses.base import BaseResponse

class UserResponse(BaseResponse):
    id: int
    name: str
    plan: str
    paid: bool
    trial_expiry: Union[str, None, datetime] = None
    email: EmailStr
    is_active: bool
    role: Role
    created_at: Union[str, None, datetime] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"

class AppInfoResponse(BaseModel):
    greeting_message: str
    disclaimers: str
    gdrive_enabled: bool
    logo_link: str