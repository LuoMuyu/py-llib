import time

from pydantic import BaseModel


class PicInfo(BaseModel):
    title: str
    url: str


class PicResponse(BaseModel):
    data: list[PicInfo]
    msg: str
    code: int = 0
    time: int = round(time.time() * 1000)
