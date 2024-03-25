from app.common.openai import openAIChat
from app.common.settings import get_settings
from app.common.vectorstore import get_vector_store_instance
from app.common.adminconfig import LLM_ROLE, LLM_PROMPT
from app.models.user import UserDocument
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.retriever import create_retriever_tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from sqlalchemy.orm import Session

settings = get_settings()

def get_qa_chain(session: Session, username):
    user_docs = session.query(UserDocument).filter_by(user_id=username).all()
    if len(user_docs) > 0:
        return construct_kb_consumer_chain(username, [f"{username}/{user_doc.document_name}" for user_doc in user_docs])
    return construct_kb_chain()

# SETUP KNOWLEDGE BASE + CONSUMER'S DOCUMENT CHAIN
def construct_kb_consumer_chain(username, consumer_doc_names):
    # get consumer retriever
    vectorstore = get_vector_store_instance(settings.PINECONE_CONSUMER_INDEX, username)

    # use "in" conditon in filter of vectorstore to compare with document ids stored in db
    consumer_retriever = vectorstore.as_retriever(search_type = "mmr", 
                                                  search_kwargs={'k': 3, 'fetch_k': 50, 'filter': {"document_id": {"$in":consumer_doc_names}}})
    consumer_retriever_tool = create_retriever_tool(
        consumer_retriever,
        "user_uploaded_file",
        "use this tool to access user's information regarding their particular scenario or circumstances"
    )

    # get knowledge base retriever
    kb_vector_store = get_vector_store_instance(settings.PINECONE_KNOWLEDGE_BASE_INDEX, None)
    kb_retriever = kb_vector_store.as_retriever(search_type="mmr", search_kwargs={'k': 3, 'fetch_k': 50})
    kb_retriever_tool = create_retriever_tool(
        kb_retriever,
        "law_knowledgebase",
        "use this tool as your core knowledge base to get any information about laws"
    )

    tools = [consumer_retriever_tool, kb_retriever_tool]

    retriever_prompt = ChatPromptTemplate.from_messages([
        ('system', f"""You are a {LLM_ROLE}. You should always use the provided tools to respond. {LLM_PROMPT}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    agent = create_openai_functions_agent(
        llm=openAIChat,
        prompt=retriever_prompt,
        tools=tools,
    )
    agentExecutor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True
    )

    return agentExecutor

# SETUP KNOWLEDGE BASE CHAIN
def construct_kb_chain():
    # get consumer retriever
    vectorstore = get_vector_store_instance(settings.PINECONE_KNOWLEDGE_BASE_INDEX, None)
    
    # get knowledge base retriever
    retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 3, 'fetch_k': 50})
    retriever_tool = create_retriever_tool(
        retriever,
        "law_search",
        "use this tool to get information about laws relevant to user's input"
    )

    tools = [retriever_tool]

    retriever_prompt = ChatPromptTemplate.from_messages([
        ('system', f"""You are a {LLM_ROLE}. You should always use the provided tool to respond. {LLM_PROMPT}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    agent = create_openai_functions_agent(
        llm=openAIChat,
        prompt=retriever_prompt,
        tools=tools,
    )
    agentExecutor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True
    )

    return agentExecutor

def get_suggested_questions_chain():
    template = """
    Based on the conversation between a user and legal writer, generate 5 PRECISE 10 WORDS follow-up questions.
    NOTE: If no conversation is provided then generate 5 PRECISE 10 WORDS questions a user can ask from a legal writer.

    Conversation:'''{chat_history}'''

    Respond ONLY with the questions without mentioning their order.
    Each question should be seperated by newline character('/n').
    Questions:"""

    prompt = ChatPromptTemplate.from_template(template)
    
    chain = (
        {"chat_history": itemgetter("chat_history")}
        | prompt
        | openAIChat
        | StrOutputParser()
    )

    return chain