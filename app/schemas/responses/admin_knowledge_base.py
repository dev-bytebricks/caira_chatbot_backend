from typing import List, Optional
from pydantic import BaseModel

class FileInfo(BaseModel):
    filename: str
    content_type: Optional[str] = None
    error: Optional[str] = None

    class Config:
        exclude_none = True

class UploadDocumentsResponse(BaseModel):
    uploaded_files: List[FileInfo]
    failed_files: List[FileInfo]

class DeleteDocumentsResponse(BaseModel):
    deleted_files: List[FileInfo]
    failed_files: List[FileInfo]

class DocumentsListResponse(BaseModel):
    files: List[FileInfo]