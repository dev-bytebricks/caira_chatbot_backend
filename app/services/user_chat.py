import re
import uuid
from fastapi import HTTPException, status
from app.common.settings import get_settings
from app.schemas.requests.user_chat import Mode
from app.common import getzep, langchain
from app.models.user import Plan, Role, User

settings = get_settings()

async def get_ai_response(user: User, db_session, user_msg, traceless, mode):
    username = user.email
    user_role = user.role
    user_plan = user.plan
    chat_history = await get_chat_history(username)

    # Check number of messages for regular user with free plan
    if user_role == Role.User and user_plan == Plan.free:
        user_message_count = 0
        for message in chat_history:
            if message.role == "User":
                user_message_count += 1
                if user_message_count == settings.FREE_PLAN_MSG_LIMIT:
                    yield "You have consumed all of your free messages. Please subscribe to continue using Caira."
                    return
    
    chat_history = chat_history[-10:]
    qa_chain = langchain.get_qa_chain(db_session, username)
    ai_msg=''

    if mode == Mode.NA:
        async for content in _stream_response(chain=qa_chain, user_msg=user_msg, zep_chat_history=chat_history):
            ai_msg += content
            yield content

        if not traceless:
            await _add_message_to_chat_history(username, "User", user_msg)
            await _add_message_to_chat_history(username, "AI", ai_msg)

    else:
        latest_ai_response = None
        for message in reversed(chat_history):
            if message.role == "AI":
                latest_ai_response = message.content
                break
        
        if latest_ai_response is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No AI response found in chat history")
        if mode == Mode.Simplify:
            user_msg = f'''Please simplify your response where you say: "{latest_ai_response}"'''
        elif mode == Mode.Elaborate:
            user_msg = f'''Please elaborate your response where you say: "{latest_ai_response}"'''
        else:
            user_msg = f'''Please give me a legal precedent on your following response: "{latest_ai_response}"'''
        
        async for content in _stream_response(chain=qa_chain, user_msg=user_msg, zep_chat_history=chat_history):
            ai_msg += content
            yield content

        if not traceless:
            await _add_message_to_chat_history(username, "AI", ai_msg)

async def _get_zep_session_id_by_username(username):
    user_all_sessions = await getzep.get_all_sessions_of_user(username)
    if len(user_all_sessions) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Zep session found")
    session_id = user_all_sessions[0].session_id
    return session_id

async def _add_message_to_chat_history(username, role, msg_content):
    session_id = await _get_zep_session_id_by_username(username)
    await getzep.add_message_to_session(session_id, role, msg_content)

async def get_chat_history(username):
    session_id = await _get_zep_session_id_by_username(username)
    return await getzep.get_all_messages_by_session(session_id)

async def get_suggested_questions(username):

    def strip_suggested_questions(question):
        question = re.sub(r'^[^a-zA-Z]+', '', question)
        question = re.sub(r'\?.*', '?', question)
        return question
    
    chat_history = await get_chat_history(username)
    chain = langchain.get_suggested_questions_chain(username)
    response = chain.invoke({"chat_history": getzep.convert_zep_messages_to_langchain(chat_history[-4:])})
    suggested_questions = response.split('\n')
    suggested_questions = [strip_suggested_questions(suggested_question) for suggested_question in suggested_questions]
    return suggested_questions

async def clear_chat_history(username):
    session_id = await _get_zep_session_id_by_username(username)
    try:
        await getzep.delete_session(session_id)
        await getzep.add_session(user_id=username, sessionid=uuid.uuid4().hex)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error occured while clearing chat history: {ex}")

async def _stream_response(chain, user_msg, zep_chat_history):
    converted_history = getzep.convert_zep_messages_to_langchain(zep_chat_history)
    async for chunk in chain.astream({"input": user_msg, "chat_history": converted_history}):
        yield chunk