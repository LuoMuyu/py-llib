# -*- coding: utf-8 -*-

import uvicorn
from fastapi import FastAPI

from app.routers import user, book, pic, video, rsa

app = FastAPI(title="图书管理系统")
app.include_router(user.router, prefix="/user", tags=["用户"])
app.include_router(book.router, prefix="/book", tags=["图书"])
app.include_router(pic.router, prefix="/pic", tags=["图片"])
app.include_router(video.router, prefix="/video", tags=["视频"])
app.include_router(rsa.router, prefix="/rsa", tags=["RSA"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
