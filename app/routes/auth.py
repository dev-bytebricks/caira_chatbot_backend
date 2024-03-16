from fastapi import APIRouter, Depends, Header, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.schemas.responses.user import LoginResponse
from app.services import auth

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "Not found"}},
)

######## Auth API Endpoints ########
@auth_router.post("/token", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def login_for_tokens(data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    return await auth.get_login_tokens(data, session)

@auth_router.post("/refresh", status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def refresh_access_token(refresh_token = Header(), session: Session = Depends(get_session)):
    return await auth.get_new_access_token(refresh_token, session)