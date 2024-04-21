from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import is_admin, oauth2_scheme, validate_access_token
from app.schemas.requests.admin_knowledge_base import ValidateDocumentsRequest, DeleteDocumentsRequest
from app.services import admin_knowledge_base

admin_knowledge_base_router_protected = APIRouter(
    prefix="/admin/knowledge-base",
    tags=["Admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token), Depends(is_admin)]
)

@admin_knowledge_base_router_protected.get("/get-azure-storage-token", status_code=status.HTTP_200_OK)
async def get_azure_storage_token():
    return await admin_knowledge_base.get_azure_storage_token()

@admin_knowledge_base_router_protected.post("/upload-gdrive")
async def upload_documents_gdrivelink(gdrivelink: str = Query(..., title="Google Drive Link"), session: Session = Depends(get_session)):
    response = await admin_knowledge_base.enqueue_gdrive_upload(gdrivelink, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@admin_knowledge_base_router_protected.get("/download/{file_name}", status_code=status.HTTP_200_OK)
async def download_document(file_name: str, session: Session = Depends(get_session)):
    return await admin_knowledge_base.get_download_link(file_name, session)

@admin_knowledge_base_router_protected.post("/delete-multiple")
async def delete_documents(data: DeleteDocumentsRequest, session: Session = Depends(get_session)):
    response = await admin_knowledge_base.enqueue_file_deletions(data.file_names, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@admin_knowledge_base_router_protected.get("/list", status_code=status.HTTP_200_OK)
async def get_documents_list(session: Session = Depends(get_session)):
    doc_list = await admin_knowledge_base.get_documents_list(session)
    return doc_list.model_dump(exclude_none=True)

@admin_knowledge_base_router_protected.post("/validate-documents", status_code=status.HTTP_200_OK)
async def validate_filenames(data: ValidateDocumentsRequest, session: Session = Depends(get_session)):
    doc_list = await admin_knowledge_base.validate_filenames(data.file_names, session)
    return doc_list.model_dump()