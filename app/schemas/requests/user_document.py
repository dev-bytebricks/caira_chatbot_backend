from typing import List
from pydantic import BaseModel
    
class DeleteDocumentsRequest(BaseModel):
    file_names: List[str]