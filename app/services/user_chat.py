import re
import uuid
from fastapi import HTTPException, status
from app.schemas.requests.user_chat import Mode
from app.schemas.responses.user_chat import AiResponse
from app.common import getzep, langchain

async def get_ai_response(username, db_session, user_msg, traceless, mode):
    chat_history = await get_chat_history(username)
    qa_chain = langchain.get_qa_chain(db_session, username)

    if mode == Mode.NA:
        qa_chain_response = qa_chain.invoke({"input": user_msg, "chat_history": getzep.convert_zep_messages_to_langchain(chat_history)})
        ai_msg = qa_chain_response["output"]
        if not traceless:
            await _add_message_to_chat_history(username, "User", user_msg)
            await _add_message_to_chat_history(username, "AI", ai_msg)
        return AiResponse(ai_response=ai_msg, traceless=traceless)
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
        qa_chain_response = qa_chain.invoke({"input": user_msg, "chat_history": getzep.convert_zep_messages_to_langchain(chat_history)})
        ai_msg = qa_chain_response["output"]
        if not traceless:
            await _add_message_to_chat_history(username, "AI", ai_msg)
        return AiResponse(ai_response=ai_msg, traceless=traceless)

async def _get_zep_session_id_by_username(username):
    user_all_sessions = getzep.get_all_sessions_of_user(username)
    if len(user_all_sessions) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Zep session found")
    session_id = user_all_sessions[0].session_id
    return session_id

async def _add_message_to_chat_history(username, role, msg_content):
    session_id = await _get_zep_session_id_by_username(username)
    getzep.add_message_to_session(session_id, role, msg_content)

async def get_chat_history(username):
    session_id = await _get_zep_session_id_by_username(username)
    return getzep.get_all_messages_by_session(session_id)

async def get_suggested_questions(username):

    def strip_suggested_questions(question):
        question = re.sub(r'^[^a-zA-Z]+', '', question)
        question = re.sub(r'\?.*', '?', question)
        return question
    
    chat_history = await get_chat_history(username)
    chain = langchain.get_suggested_questions_chain()
    response = chain.invoke({"chat_history": getzep.convert_zep_messages_to_langchain(chat_history[-4:])})
    suggested_questions = response.split('\n')
    suggested_questions = [strip_suggested_questions(suggested_question) for suggested_question in suggested_questions]
    return suggested_questions

async def clear_chat_history(username):
    session_id = await _get_zep_session_id_by_username(username)
    try:
        getzep.delete_session(session_id)
        getzep.add_session(user_id=username, sessionid=uuid.uuid4().hex)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error occured while clearing chat history: {ex}")