from app.common.settings import get_settings
from app.common.vectorstore import get_vector_store_instance
from app.common.adminconfig import AdminConfig
from app.models.user import UserDocument, KnowledgeBaseDocument
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel
from operator import itemgetter
from sqlalchemy.orm import Session


settings = get_settings()

def get_qa_chain(session: Session, username, llm_primary, llm_secondary):
    kb_docs = session.query(KnowledgeBaseDocument).filter_by(
        status="Completed").all()
    user_docs = session.query(UserDocument).filter_by(
        user_id=username,
        status="Completed").all()
    
    if len(user_docs) > 0:
        consumer_retrieval = __get_consumer_retriever_tool(llm_secondary, [f"{username}:{user_doc.document_name}:" for user_doc in user_docs], 3)
        kb_retrieval = __get_kb_retriever_tool(llm_secondary, [f'{kb_doc.document_name}:' for kb_doc in kb_docs], 3)
        return construct_kb_consumer_chain(username, llm_primary, consumer_retrieval, kb_retrieval)
    
    
    kb_retrieval = __get_kb_retriever_tool(llm_secondary, [kb_doc.document_name for kb_doc in kb_docs], 4)
    return construct_kb_chain(username, llm_primary, kb_retrieval)

# SETUP KNOWLEDGE BASE + CONSUMER'S DOCUMENT CHAIN
def construct_kb_consumer_chain(username, llm, consumer_retriever_tool, kb_retriever_tool):

    prompt = ChatPromptTemplate.from_messages([
        ('system', f"You are a {AdminConfig.LLM_ROLE}.\n{AdminConfig.LLM_PROMPT}." +        
        "\n\nYou should ALWAYS and ONLY reference the following cases and legal acts to support your answer:'''{laws_from_kb}'''" +
        "\n\nUser's Scenario:\n'''{user_scenario}'''"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    
    output_parser = StrOutputParser()
    setup_and_retrieval = RunnableParallel(
        {"user_scenario": consumer_retriever_tool, "laws_from_kb": kb_retriever_tool, "input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
    )

    chain = (
        setup_and_retrieval
        | prompt
        | llm
        | output_parser
    ).with_config({"tags": ["execute-kb+docs-retriever-agent"], "metadata": {"user-email": username}})
    
    return chain

# SETUP KNOWLEDGE BASE CHAIN
def construct_kb_chain(username, llm, kb_retriever_tool):    
    prompt = ChatPromptTemplate.from_messages([
        ('system', f"You are a {AdminConfig.LLM_ROLE}.\n{AdminConfig.LLM_PROMPT}." +        
        "\n\nYou should ALWAYS and ONLY reference the following cases and legal acts to support your answer:'''{laws_from_kb}'''"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
    
    output_parser = StrOutputParser()
    setup_and_retrieval = RunnableParallel(
        {"laws_from_kb": kb_retriever_tool, "input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
    )

    chain = (
        setup_and_retrieval
        | prompt
        | llm
        | output_parser
    ).with_config({"tags": ["execute-kb-retriever-agent"], "metadata": {"user-email": username}})
    
    return chain

def __get_kb_retriever_tool(llm, kb_doc_names, top_k):
    vectorstore = get_vector_store_instance(settings.PINECONE_KNOWLEDGE_BASE_INDEX, None)
    retriever = vectorstore.as_retriever(search_type="mmr", 
                                         search_kwargs={
                                             'k': top_k, 
                                             'fetch_k': 50,
                                             'filter': {"file_name": {"$in": kb_doc_names}}
                                             })

    template = """
    You are an experienced solicitor and have access to knowledge base of cases and legal acts.
    You have been tasked to output three keyword-based search queries to fetch relevant pieces of information from cases and legal acts.
    Use the below conversation between a user and legal writer to generate the search queries.
    
    Conversation:'''{chat_history}'''

    Latest Message:'''{input}'''
    
    Respond ONLY with three different search queries, each targeting a different angle.

    Search Queries:"""

    retriever_prompt = ChatPromptTemplate.from_template(template)

    return create_history_aware_retriever(
        llm=llm,
        retriever=retriever,
        prompt=retriever_prompt
    )

def __get_consumer_retriever_tool(llm, consumer_doc_names, top_k):
    vectorstore = get_vector_store_instance(settings.PINECONE_CONSUMER_INDEX, None)
    retriever = vectorstore.as_retriever(search_type = "mmr", 
                                                  search_kwargs={
                                                      'k': top_k, 
                                                      'fetch_k': 50,
                                                      'filter': {"file_name": {"$in": consumer_doc_names}}
                                                     })
    
    template = """
    You are an expert in generating keyword-based search queries to extract relevant sections from a document.
    Your task is to analyse the on going conversation between the user and the assitant below and output three keyword-based search queries.
    The search queries will be used to fetch relevant sections from the user's document.

    Conversation:'''{chat_history}'''

    Latest Message:'''{input}'''
    
    Respond ONLY with three different search queries, each targeting a different angle.

    Search Queries:"""

    retriever_prompt = ChatPromptTemplate.from_template(template)

    return create_history_aware_retriever(
        llm=llm,
        retriever=retriever,
        prompt=retriever_prompt
    )

def get_suggested_questions_chain(username, llm):
    template = """
    Based on the conversation between a user and legal writer, generate 5 PRECISE 5 WORDS follow-up questions.
    NOTE: If no conversation is provided then generate 5 PRECISE 5 WORDS questions a user can ask from a legal writer.

    Conversation:'''{chat_history}'''

    Respond ONLY with the questions without mentioning their order.
    Each question should be seperated by newline character('/n').
    Questions:"""

    prompt = ChatPromptTemplate.from_template(template)
    
    chain = (
        {"chat_history": itemgetter("chat_history")}
        | prompt
        | llm
        | StrOutputParser()
    ).with_config({"tags": ["execute-suggested-question-chain"], "metadata": {"user-email": username}})

    return chain