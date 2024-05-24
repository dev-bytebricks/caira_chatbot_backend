from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token, get_current_user
from app.schemas.responses.user import UserResponse, AppInfoResponse
from app.schemas.requests.user import RegisterUserRequest, VerifyUserRequest, EmailRequest, ResetRequest, DeleteUserRequest
from app.services import user

# For Unprotected User Endpoints
user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

# For Protected User Endpoints
user_router_protected = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token)]
)

######## Users API Unsecured Endpoints ########
@user_router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: EmailRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    await user.email_forgot_password_link(data, session, background_tasks)
    return JSONResponse({"message": "An email with password reset link has been sent to you."})

@user_router.put("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetRequest, session: Session = Depends(get_session)):
    await user.reset_user_password(data, session)
    return JSONResponse({"message": "Your password has been updated."})

@user_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(data: RegisterUserRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    return await user.create_user_account(data, session, background_tasks)

@user_router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user(data: VerifyUserRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    await user.activate_user_account(data, session, background_tasks)
    return JSONResponse({"message": "Account is activated successfully."})

@user_router.post("/delete", status_code=status.HTTP_200_OK)
async def delete_user(data: DeleteUserRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    await user.delete_user(data, session)
    return JSONResponse({"message": "Account has been deleted successfully."})

######## Users API Secured Endpoints ########
@user_router_protected.get("/me", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def fetch_user(user = Depends(get_current_user)):
    return user

@user_router_protected.post("/request-delete", status_code=status.HTTP_200_OK)
async def delete_user(background_tasks: BackgroundTasks, userdata = Depends(get_current_user)):
    await user.request_user_delete(userdata, background_tasks)
    return JSONResponse({"message": "A verification email has been sent"})

@user_router_protected.get("/app-info", status_code=status.HTTP_200_OK, response_model=AppInfoResponse)
async def fetch_app_info(session: Session = Depends(get_session)):
    return await user.fetch_app_info(session)

@user_router_protected.get("/logout", status_code=status.HTTP_200_OK)
async def logout_user(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    await user.logout_user(username, session)
    return JSONResponse({"message": "You have been logged out successfully."})

@user_router_protected.get("/pubsub-token", status_code=status.HTTP_200_OK)
async def generate_pubsub_client_token(userdata = Depends(get_current_user)):
    return await user.generate_pubsub_client_token(userdata)