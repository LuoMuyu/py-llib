import time

from pydantic import BaseModel


class UserDataBase(BaseModel):
    id: int
    create_time: int
    email: str
    email_verification_token: str
    email_verified: bool
    id_card: str
    password: str
    permission: int
    phone: str
    phone_code_expire_time: int
    phone_verification_code: str
    phone_verified: bool
    real_name: str
    realname_verified: bool
    salt: str
    username: str


class UserInfo(BaseModel):
    username: str
    email: str
    permission: int
    phone: str = None


class PhoneInfo(BaseModel):
    phone: str
    phoneVerificationCode: str
    phoneCodeExpireTime: int
    phoneVerified: bool


class RealNameInfo(BaseModel):
    realname: str
    idcard: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class PhoneRequest(BaseModel):
    username: str
    phone: str


class PhoneVerifyRequest(BaseModel):
    username: str
    phone: str
    code: str


class RealNameRequest(BaseModel):
    username: str
    realname: str
    idcard: str


class LoginResponse(BaseModel):
    msg: str
    token: str
    data: UserInfo
    code: int = 0
    time: int = round(time.time() * 1000)


class EmailResponse(BaseModel):
    msg: str
    token: str
    email: str
    code: int = 0
    time: int = round(time.time() * 1000)
