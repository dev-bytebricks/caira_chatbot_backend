from pydantic import BaseModel, EmailStr
from app.models.user import Role

class RegisterUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role

class VerifyUserRequest(BaseModel):
    token: str
    email: EmailStr

class DeleteUserRequest(BaseModel): 
    token: str
    email: EmailStr
    
class EmailRequest(BaseModel):
    email: EmailStr
    
class ResetRequest(BaseModel):
    token: str
    email: EmailStr
    password: str
    