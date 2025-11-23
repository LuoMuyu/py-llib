from fastapi import HTTPException, Request

from app.utils.jwt import JWT
from app.utils.user import User


def get_current_user(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = JWT.parse_claim(token)
    username = payload.get("name")
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User(username).select_by_username()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
