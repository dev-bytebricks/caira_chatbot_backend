from sqlalchemy.dialects.mysql import DATETIME
import enum
from sqlalchemy import Boolean, Column, Integer, Numeric, String, ForeignKey, Enum, Text, func, Index
from app.common.database import Base
from sqlalchemy.orm import mapped_column, relationship

class Role(enum.Enum):
    User = 0
    Admin = 1

class Plan(enum.Enum):
    free = "Free"
    one_month = "One Month"
    three_month = "Three Month"
    six_month = "Six Month"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150))
    email = Column(String(255), unique=True, index=True)
    paid = Column(Boolean, default=False)
    plan = Column(Enum(Plan), nullable=True)
    stripeId = Column(String(200), nullable=True)
    password = Column(String(100))
    is_active = Column(Boolean, default=False)
    role = Column(Enum(Role), nullable=False)
    verified_at = Column(DATETIME(fsp=3), nullable=True, default=None)
    trial_expiry = Column(DATETIME(fsp=3), nullable=True, default=None)
    updated_at = Column(DATETIME(fsp=3), nullable=True, default=None, onupdate=func.now())
    created_at = Column(DATETIME(fsp=3), nullable=False, default=func.now())
    
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("UserDocument", back_populates="user", cascade="all, delete-orphan")

    def get_context_string(self, context: str):
        return f"{context}{self.password[-6:]}{self.updated_at.strftime('%m%d%Y%H%M%S')}".strip()
    
class UserToken(Base):
    __tablename__ = "user_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey('users.email'))
    refresh_token = Column(String(250), nullable=True, index=True, default=None)
    created_at = Column(DATETIME(fsp=3), nullable=False, default=func.now())
    expires_at = Column(DATETIME(fsp=3), nullable=False)
    
    user = relationship("User", back_populates="tokens")

class UserDocument(Base):
    __tablename__ = "user_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey('users.email'))
    document_name = Column(String(length=250, collation="utf8mb3_bin"), nullable=True, index=True, default=None)
    content_type = Column(String(250), nullable=True, index=True, default=None)
    status = Column(String(100), nullable=True, index=True, default=None)
    updated_at = Column(DATETIME(fsp=3), nullable=True, default=None, onupdate=func.now())
    created_at = Column(DATETIME(fsp=3), nullable=False, default=func.now())

    __table_args__ = (
        Index("idx_user_id_document_name", "user_id", "document_name"),
        Index("idx_user_id_document_name_status", "user_id", "document_name", "status"),
    )

    user = relationship("User", back_populates="documents")

class AdminConfig(Base):
    __tablename__ = "admin_config"
    id = Column(Integer, primary_key=True)
    llm_model_name = Column(String(250), nullable=False, index=True, default=None)
    llm_temperature = Column(Numeric(2,2), nullable=False, default=None)
    llm_streaming = Column(Boolean, nullable=False, default=True)
    llm_prompt = Column(Text, nullable=False, default=None)
    llm_role = Column(String(100), nullable=False, default=None)
    llm_streaming = Column(Boolean, nullable=False, default=True)
    greeting_message = Column(String(250), nullable=False, default=None)
    disclaimers = Column(String(500), nullable=False, default=None)
    gdrive_enabled = Column(Boolean, nullable=False, default=False)
    logo_link = Column(String(250), nullable=False, default=None)
    updated_at = Column(DATETIME(fsp=3), nullable=False, default=func.now())

class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledgebase_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(length=250, collation="utf8mb3_bin"), nullable=True, index=True, default=None)
    content_type = Column(String(250), nullable=True, index=True, default=None)
    status = Column(String(100), nullable=True, index=True, default=None)
    updated_at = Column(DATETIME(fsp=3), nullable=True, default=None, onupdate=func.now())
    created_at = Column(DATETIME(fsp=3), nullable=False, default=func.now())

    __table_args__ = (
        Index("idx_document_name_status", "document_name", "status"),
    )