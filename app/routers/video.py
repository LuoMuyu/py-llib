from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Request, Query
from starlette.responses import StreamingResponse

from app.utils.video import Video

router = APIRouter()
BASE_DIR = Path(__file__).parent.parent / "videos"


@router.get("/play")
async def video_play(request: Request, filename: Optional[str] = Query(default=None)):
    return Video().get_random_video(str(request.base_url), filename)


@router.get("/{filename}")
async def video(filename: str):
    file_path = (BASE_DIR / filename).resolve()

    if not file_path.is_file() or BASE_DIR not in file_path.parents:
        return {"error": "File not found"}

    async def interfile():
        try:
            async with aiofiles.open(file_path, mode="rb") as f:
                while chunk := await f.read(1024 * 1024):
                    yield chunk
        except (ConnectionResetError, BrokenPipeError):
            return

    return StreamingResponse(interfile(), media_type="mp4", headers={"Accept-Ranges": "bytes"})
