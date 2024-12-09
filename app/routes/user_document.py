from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token, get_current_user
from app.schemas.requests.user_document import DeleteDocumentsRequest, ValidateDocumentsRequest
from app.services import user_document
from fastapi import FastAPI, File, UploadFile, HTTPException


user_document_router_protected = APIRouter(
    prefix="/users/documents",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token)]
)

@user_document_router_protected.post("/upload-files", status_code=status.HTTP_200_OK)
async def upload_file(files: list[UploadFile],username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    allowed_extensions = {".pdf", ".txt"}
    print(f'upload files are these shown {files}')
    for file in files:
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is not allowed. Only PDF and TXT files are supported."
            )
    await user_document.manage_upload_file(files, username, session)
    return {"filenames": [file.filename for file in files]}

# @user_document_router_protected.get("/get-azure-storage-token", status_code=status.HTTP_200_OK)
# async def get_azure_storage_token():
#     return await user_document.get_azure_storage_token()

# @user_document_router_protected.post("/upload-gdrive")
# async def upload_documents_gdrivelink(gdrivelink: str = Query(..., title="Google Drive Link"), userdata = Depends(get_current_user), session: Session = Depends(get_session)):
#     response = await user_document.enqueue_gdrive_upload(gdrivelink, userdata, session)
#     status_code = status.HTTP_200_OK
#     if len(response.failed_files) > 0:
#         status_code = status.HTTP_417_EXPECTATION_FAILED
#     return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@user_document_router_protected.get("/download/{file_name}", status_code=status.HTTP_200_OK)
async def download_document(file_name: str, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    return await user_document.get_download_link(username, file_name, session)

@user_document_router_protected.post("/delete-multiple")
async def enqueue_file_deletions(data: DeleteDocumentsRequest, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    #response = await user_document.enqueue_file_deletions(username, data.file_names, session)
    response = await user_document.delete_files_from_db(username, data.file_names, session)
    status_code = status.HTTP_200_OK
    if len(response.failed_files) > 0:
        status_code = status.HTTP_417_EXPECTATION_FAILED
    return JSONResponse(status_code=status_code, content=response.model_dump(exclude_none=True))

@user_document_router_protected.get("/list", status_code=status.HTTP_200_OK)
async def get_documents_list(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    doc_list = await user_document.get_documents_list(username, session)
    return doc_list.model_dump(exclude_none=True)

@user_document_router_protected.post("/validate-documents", status_code=status.HTTP_200_OK)
async def validate_filenames(data: ValidateDocumentsRequest, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    doc_list = await user_document.validate_filenames(username, data.file_names, session)
    return doc_list.model_dump()