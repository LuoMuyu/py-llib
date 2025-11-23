from sqlalchemy import Column, String, Boolean, Integer
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    create_time = Column(Integer, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    email_verification_token = Column(String(64), nullable=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    id_card = Column(String(18), unique=True, index=True, nullable=True)
    password = Column(String(128), nullable=False)
    permission = Column(Integer, nullable=False)
    phone = Column(String(11), unique=True, index=True, nullable=True)
    phone_code_expired_time = Column(Integer, nullable=True)
    phone_verification_code = Column(String(6), nullable=True)
    phone_verified = Column(Boolean, nullable=False, default=False)
    real_name = Column(String(50), nullable=True)
    realname_verified = Column(Boolean, nullable=False, default=False)
    salt = Column(String(32), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)

