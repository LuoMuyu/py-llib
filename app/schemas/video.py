import time

from pydantic import BaseModel


class VideoInfo(BaseModel):
    title: str
    description: str
    url: str
    like: int
    comment: int


class VideoResponse(BaseModel):
    video: VideoInfo
    next: VideoInfo | None
    msg: str
    code: int = 0
    time: int = round(time.time() * 1000)
