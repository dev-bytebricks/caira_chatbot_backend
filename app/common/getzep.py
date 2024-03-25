from app.common.settings import get_settings
from zep_python import ZepClient, exceptions as zep_exceptions
from zep_python.user import CreateUserRequest
from zep_python.memory.models import Session
from zep_python.memory import Memory, Message
from langchain_core.messages import AIMessage, HumanMessage
import datetime

settings = get_settings()

zep_client = ZepClient(settings.ZEP_API_URL)

def get_all_users():
    return zep_client.user.list(limit=1000, cursor=0)

def delete_user(user_id):
    zep_client.user.delete(user_id)

def check_user_exists(user_id):
    try:
        if zep_client.user.get(user_id):
            return True
        return False
    except zep_exceptions.NotFoundError:
        return False

def add_new_user(user_id, emailid, full_name):
    user_request = CreateUserRequest(
        user_id=user_id,
        email=emailid,
        first_name=full_name,
        last_name="",
        metadata={"created_timestamp": str(datetime.datetime.now())}
    )
    zep_client.user.add(user_request)
    print(f'user with id {user_id} created in zep')

def get_all_sessions():
    return zep_client.memory.list_sessions(limit=1000, cursor=0)

def get_all_sessions_of_user(user_id):
    return zep_client.user.get_sessions(user_id)

def add_session(user_id, sessionid):
    session = Session(
        session_id=sessionid,
        user_id=user_id,
        metadata={"created_timestamp": str(datetime.datetime.now())}
        )
    zep_client.memory.add_session(session)
    print(f'session for user {user_id} created in zep')

def retrieve_zep_memory(session_id):
    messages_list = []
    memory = zep_client.memory.get_memory(session_id)
    for message in memory.messages:
        messages_list.append({"role":message.role, "content":message.content})
    return messages_list

def delete_session(session_id):
    print(f'deleting session from zep, session_id: {session_id}')
    print(zep_client.memory.delete_memory(session_id))
    print(f'session deleted from zep, session_id: {session_id}')

def convert_zep_messages_to_langchain(conversation_from_zep):
    langchain_chat_history = []
    for message in conversation_from_zep:
        if message.role == "User":
            langchain_chat_history.append(HumanMessage(content=message.content))
        else:
            langchain_chat_history.append(AIMessage(content=message.content))
    return langchain_chat_history

def get_all_messages_by_session(session_id):
    return zep_client.message.get_session_messages(session_id)
    
def add_message_to_session(session_id, role, msg_content):
    response = zep_client.memory.add_memory(session_id, Memory(messages=[Message(role=role, content=msg_content)]))
    print(f"chatbot response added to zep: {response}")