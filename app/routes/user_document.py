from typing import List
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token
from app.schemas.requests.user_document import DeleteDocumentsRequest
from app.schemas.responses.user_document import DeleteDocumentsResponse, DocumentsListResponse, UploadDocumentsResponse
from app.services import user_document

user_document_router_protected = APIRouter(
    prefix="/users/documents",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token)]
)

# process manually uploaded documents and upload them to vectorstore and azure storage
# users/documents -> Post Request, Request body: multi part form data, response: list of uploaded documents
@user_document_router_protected.post("/upload", response_model=UploadDocumentsResponse)
async def upload_documents(files: List[UploadFile] = File(...), username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    response = await user_document.upload_documents(files, username, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump())

# process google drive link and upload them to vectorstore and azure storage
# users/documents -> Post Request, Request body: link to googledrive file/folder, respose: list of uploaded documents
@user_document_router_protected.post("/upload-gdrive", response_model=UploadDocumentsResponse)
async def upload_documents_gdrivelink(gdrivelink: str = Query(..., title="Google Drive Link"), username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    response = await user_document.upload_documents_gdrivelink(gdrivelink, username, session)
    status_code = status.HTTP_200_OK
    if len(response["failed_files"]) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response)

# download uploaded documents from azure storage
# users/documents -> Get Request, path parameter: file_name, Response Body: Document download link
@user_document_router_protected.get("/download/{file_name}", status_code=status.HTTP_200_OK)
async def download_document(file_name: str, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    return await user_document.get_download_link(username, file_name, session)

@user_document_router_protected.post("/delete-multiple", response_model=DeleteDocumentsResponse)
async def delete_documents(data: DeleteDocumentsRequest, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    response = await user_document.delete_documents(data.file_names, username, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump())

# get uploaded documents list from azure storage
# users/documents/list -> Get Request, Response body: list of document details
@user_document_router_protected.get("/list", status_code=status.HTTP_200_OK)
async def get_documents_list(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    doc_list = await user_document.get_documents_list(username, session)
    return doc_list.model_dump(exclude_none=True)

