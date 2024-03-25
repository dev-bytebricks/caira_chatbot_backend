from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.common.database import get_session
from app.common.security import oauth2_scheme, validate_access_token
from app.schemas.responses.user_chat import AiResponse, ChatHistoryResponse, ChatMessage
from app.schemas.requests.user_chat import AiRequest
from app.services import user_chat

user_chat_router_protected = APIRouter(
    prefix="/users/chat",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(oauth2_scheme), Depends(validate_access_token)]
)

# check if user has uploaded any document to use the retriever chain. (store the status of document uploaded in db)
# users/chat/send-msg -> Post Request, Request body: Mode: 0, User-Msg: "xyz", Traceless: False, Response: ai response, Traceless: False
# The modes will be stored in form of enums (0 - N/A, 1 - Simplify, 2 - Elaborate, 3 - Get Legal Precedent)
@user_chat_router_protected.post("/send-msg", status_code=status.HTTP_200_OK, response_model=AiResponse)
async def get_ai_response(data: AiRequest, username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    return await user_chat.get_ai_response(username, session, data.user_msg, data.traceless, data.mode)

# Get chat history
# users/chat/get-msgs -> Get Request, Response: list of msgs
@user_chat_router_protected.get("/get-msgs", status_code=status.HTTP_200_OK, response_model=ChatHistoryResponse)
async def get_chat_history(username: str = Depends(validate_access_token)):
    msgs = await user_chat.get_chat_history(username)
    msgs = [ChatMessage(role=msg.role, content=msg.content, created_at=msg.created_at) for msg in msgs]
    return ChatHistoryResponse(messages=msgs)

# users/chat/suggested-qs -> Get Request, Response body: Suggested Questions: List of string
@user_chat_router_protected.get("/suggested-qs", status_code=status.HTTP_200_OK)
async def get_suggested_questions(username: str = Depends(validate_access_token)):
    return await user_chat.get_suggested_questions(username)

@user_chat_router_protected.delete("/clear-chat", status_code=status.HTTP_200_OK)
async def clear_chat_history(username: str = Depends(validate_access_token)):
    await user_chat.clear_chat_history(username)
    return JSONResponse({"message": "Your chat history has been cleared."})


