from typing import List, Optional
from pydantic import BaseModel

class FileInfo(BaseModel):
    filename: str
    content_type: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None

    class Config:
        exclude_none = True

class GdriveUploadResponse(BaseModel):
    queued_files: List[FileInfo]
    failed_files: List[FileInfo]

class DeleteDocumentsResponse(BaseModel):
    failed_files: List[FileInfo]

class FileExists(BaseModel):
    filename: str
    exists: bool

class ValidateDocumentsResponse(BaseModel):
    files: List[FileExists]

class DocumentsListResponse(BaseModel):
    uploaded_files: List[FileInfo]
    processing_files: List[FileInfo]
    failed_files: List[FileInfo]