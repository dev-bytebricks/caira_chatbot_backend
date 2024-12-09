
from app.models.user import UserDocument,KnowledgeBaseDocument
from app.common.database import get_dependency_free_session
from sqlalchemy.orm import joinedload

#user database helpers
def get_file_from_user_db(user_id, file_name):
    try:
        with get_dependency_free_session() as session:
            user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
                .filter(UserDocument.user_id == user_id, UserDocument.document_name == file_name).first()
            return user_doc
    except Exception as ex:
        raise Exception(f"is_file_in_user_db | Error occured while performing db operation: {ex}")
    finally:
        session.close()
    
def create_user_file_entry(user_name, file_name, status, content_type):
    try:
        with get_dependency_free_session() as session:
            session.add(UserDocument(user_id=user_name, document_name=file_name, content_type=content_type, status=status))
            session.commit()
    except Exception as ex:
        raise Exception(f"create_user_file_entry | Error occured while performing db operation: {ex}")
    finally:
        session.close()

def update_user_file_entry(user_id, file_name, status):
    try:
        with get_dependency_free_session() as session:
            user_doc = session.query(UserDocument).options(joinedload(UserDocument.user))\
                .filter(UserDocument.user_id == user_id, UserDocument.document_name == file_name).first()
            user_doc.status = status
            session.add(user_doc)
            session.commit()
    except Exception as ex:
        raise Exception(f"update_user_file_entry | Error occured while performing db operation: {ex}")        
    finally:
        session.close()

def delete_user_file_entry(user_name, file_name):
    try:
        with get_dependency_free_session() as session:
            session.query(UserDocument)\
                .filter(UserDocument.user_id == user_name, UserDocument.document_name == file_name).delete(synchronize_session='fetch')
            session.commit()
    except Exception as ex:
        raise Exception(f"delete_user_file_entry | Error occured while performing db operation: {ex}")       
    finally:
        session.close()

#KB database helpers
def get_file_from_kb_db(file_name):
    try:
        with get_dependency_free_session() as session:
            kb_doc = session.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.document_name == file_name).first()
            return kb_doc
    except Exception as ex:
        raise Exception(f"is_file_in_kb_db | Error occured while performing db operation: {ex}")  
    finally:
        session.close()
    
def create_kb_file_entry(file_name, status, content_type):
    try:
        with get_dependency_free_session() as session:
            session.add(KnowledgeBaseDocument(document_name=file_name, content_type=content_type, status=status))
            session.commit()
    except Exception as ex:
        raise Exception(f"create_kb_file_entry | Error occured while performing db operation: {ex}")  
    finally:
        session.close()

def update_kb_file_entry(file_name, status):
    try:
        with get_dependency_free_session() as session:
            kb_doc = session.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.document_name == file_name).first()
            kb_doc.status = status
            session.add(kb_doc)
            session.commit()
    except Exception as ex:
        raise Exception(f"update_kb_file_entry | Error occured while performing db operation: {ex}")  
    finally:
        session.close()

def delete_kb_file_entry(file_name):
    try:
        with get_dependency_free_session() as session:
            session.query(KnowledgeBaseDocument)\
                .filter(KnowledgeBaseDocument.document_name == file_name).delete(synchronize_session='fetch')
            session.commit()
    except Exception as ex:
        raise Exception(f"delete_kb_file_entry | Error occured while performing db operation: {ex}")
    finally:
        session.close()