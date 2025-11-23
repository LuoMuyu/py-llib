from functools import wraps

from fastapi import HTTPException

from app.schemas.common import ResponseNormal, DataResponse


def handle_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if isinstance(result, (ResponseNormal, DataResponse)):
            return result

        if result is True:
            return ResponseNormal(msg="操作成功")

        if result in (False, None):
            return ResponseNormal(msg="操作失败", code=1)

        return DataResponse(msg="操作成功", data=result)

    return wrapper


def require_permission(level: int = 1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            if user.permission > level:
                raise HTTPException(status_code=403, detail="权限不足")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def match_username(param_name: str = "username"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            username = kwargs.get(param_name)
            if username and user and username != user.username:
                return ResponseNormal(msg="用户名不匹配", code=1)
            return func(*args, **kwargs)

        return wrapper

    return decorator
