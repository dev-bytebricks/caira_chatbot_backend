from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token
from app.schemas.requests.user_document import DeleteDocumentsRequest, ValidateDocumentsRequest
from app.services import user_document

user_document_router_protected = APIRouter(
    prefix="/users/documents",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token)]
)

@user_document_router_protected.get("/get-azure-storage-token", status_code=status.HTTP_200_OK)
async def get_azure_storage_token():
    return await user_document.get_azure_storage_token()

@user_document_router_protected.post("/upload-gdrive")
async def upload_documents_gdrivelink(gdrivelink: str = Query(..., title="Google Drive Link"), username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    response = await user_document.enqueue_gdrive_upload(gdrivelink, username, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@user_document_router_protected.get("/download/{file_name}", status_code=status.HTTP_200_OK)
async def download_document(file_name: str, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    return await user_document.get_download_link(username, file_name, session)

@user_document_router_protected.post("/delete-multiple")
async def enqueue_file_deletions(data: DeleteDocumentsRequest, username: str = Depends(validate_access_token)):
    response = await user_document.enqueue_file_deletions(username, data.file_names)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@user_document_router_protected.get("/list", status_code=status.HTTP_200_OK)
async def get_documents_list(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    doc_list = await user_document.get_documents_list(username, session)
    return doc_list.model_dump(exclude_none=True)

@user_document_router_protected.post("/validate-documents", status_code=status.HTTP_200_OK)
async def get_documents_list(data: ValidateDocumentsRequest, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    doc_list = await user_document.validate_filenames(username, data.file_names, session)
    return doc_list.model_dump()