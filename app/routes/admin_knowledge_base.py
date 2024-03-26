from typing import List
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import is_admin, oauth2_scheme, validate_access_token
from app.schemas.requests.user_document import DeleteDocumentsRequest
from app.services import admin_knowledge_base

admin_knowledge_base_router_protected = APIRouter(
    prefix="/admin/knowledge-base",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token), Depends(is_admin)]
)

@admin_knowledge_base_router_protected.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...), session: Session = Depends(get_session)):
    response = await admin_knowledge_base.upload_documents(files, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@admin_knowledge_base_router_protected.post("/upload-gdrive")
async def upload_documents_gdrivelink(gdrivelink: str = Query(..., title="Google Drive Link"), session: Session = Depends(get_session)):
    response = await admin_knowledge_base.upload_documents_gdrivelink(gdrivelink, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@admin_knowledge_base_router_protected.get("/download/{file_name}", status_code=status.HTTP_200_OK)
async def download_document(file_name: str, session: Session = Depends(get_session)):
    return await admin_knowledge_base.get_download_link(file_name, session)

@admin_knowledge_base_router_protected.post("/delete-multiple")
async def delete_documents(data: DeleteDocumentsRequest, session: Session = Depends(get_session)):
    response = await admin_knowledge_base.delete_documents(data.file_names, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@admin_knowledge_base_router_protected.get("/list", status_code=status.HTTP_200_OK)
async def get_documents_list(session: Session = Depends(get_session)):
    doc_list = await admin_knowledge_base.get_documents_list(session)
    return doc_list.model_dump(exclude_none=True)

