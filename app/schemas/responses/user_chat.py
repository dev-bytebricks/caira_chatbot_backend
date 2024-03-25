from datetime import datetime
from typing import List
from pydantic import BaseModel

class AiResponse(BaseModel):
    ai_response: str
    traceless: bool

class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
