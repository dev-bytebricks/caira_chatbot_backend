from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token, is_admin
from app.schemas.responses.admin import AdminConfigResponse
from app.schemas.requests.admin import UpdateAdminConfigRequest
from app.services import admin

admin_router_protected = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token), Depends(is_admin)]
)

@admin_router_protected.post("/config", status_code=status.HTTP_200_OK)
async def update_admin_config(data: UpdateAdminConfigRequest, session: Session = Depends(get_session)):
    await admin.update_admin_config(data, session)
    return JSONResponse({"message": "Admin config has been updated"})

@admin_router_protected.get("/config", status_code=status.HTTP_200_OK, response_model=AdminConfigResponse)
async def get_admin_config(session: Session = Depends(get_session)):
    return await admin.get_admin_config(session)