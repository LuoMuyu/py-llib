from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.schemas.user import *
from app.schemas.common import *
from app.utils.decorators import handle_response, match_username, require_permission
from app.utils.jwt import JWT
from app.utils.register import Register
from app.utils.login import Login
from app.utils.user import User
from app.utils.email import Email
from app.utils.phone import Phone
from app.utils.realname import RealName
from app.utils import r

router = APIRouter()


@router.post("/register")
def register(req: RegisterRequest):
    return Register(req.username, req.password, req.email).register()


@router.get("/resendEmail")
@match_username("username")
def resend_email(user=Depends(get_current_user)):
    return Email(user.username).resend_email()


@router.get("/verifyEmail")
def verify_email(token: str):
    data = Email().verify_email(token)
    if not data:
        return False

    access_token = r.get(data['username']) or JWT.gen_access_token(data['username'])
    if not r.get(data['username']):
        r.set(data['username'], access_token, 60 * 60 * 24)

    return EmailResponse(msg="邮件验证成功", email=data['email'], token=access_token)


@router.post("/login")
def login(req: LoginRequest):
    user = Login(req.username, req.password).login()
    if not user:
        return ResponseNormal(msg="用户名或密码错误", code=1)

    access_token = r.get(user.username) or JWT.gen_access_token(user.username)
    if not r.get(user.username):
        r.set(user.username, access_token, 60 * 60 * 24)

    return LoginResponse(token=access_token, data=user, msg="登录成功")


@router.get("/logout")
@handle_response
def logout(user=Depends(get_current_user)):
    r.delete(user.username)
    return True


@router.get("/getUserInfo")
@handle_response
def get_user_info(user=Depends(get_current_user)):
    return user


@router.get("/getAllUserInfo")
@require_permission(level=0)
def get_all_user_info(user=Depends(get_current_user)):
    users = User(user.username).select_all()
    return DataResponse(
        msg="获取用户信息成功",
        data=users
    )


@router.post("/sendPhoneCode")
@handle_response
@match_username("username")
def send_phone_code(req: PhoneRequest, user=Depends(get_current_user)):
    phone_info = User(user.username).get_phone_info()
    if phone_info:
        return False

    phone = Phone(user.username, req.phone)
    if not phone.validate():
        return False

    return phone.send_code()


@router.post("/verifyPhone")
@handle_response
@match_username("username")
def verify_phone(req: PhoneVerifyRequest, user=Depends(get_current_user)):
    phone = Phone(user.username, req.phone)
    return phone.verify_code(req.code)


@router.post("/realName")
@handle_response
@match_username("username")
def real_name(req: RealNameRequest, user=Depends(get_current_user)):
    data = RealName(user, req.realname, req.idcard).verify()
    return data


@router.get("/getRealName")
@handle_response
def get_real_name(user=Depends(get_current_user)):
    data = RealName(user).get_masked_real_name()
    return data
