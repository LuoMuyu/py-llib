import time
from typing import Any

from pydantic import BaseModel


class ResponseNormal(BaseModel):
    msg: str
    code: int = 0
    time: int = round(time.time() * 1000)


class DataResponse(BaseModel):
    msg: str
    data: Any
    code: int = 0
    time: int = round(time.time() * 1000)


class RSAResponse(BaseModel):
    publicKey: str
    code: int = 0
    time: int = round(time.time() * 1000)
