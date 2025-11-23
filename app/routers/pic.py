import mimetypes
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.utils.pic import Pic

router = APIRouter()
BASE_DIR = Path(__file__).parent.parent / "images"


@router.get("/list")
async def pic_play(request: Request):
    return Pic().get_pic_list(str(request.base_url))


@router.get("/{filename}")
async def image(filename: str):
    file_path = (BASE_DIR / filename).resolve()

    if not file_path.is_file() or BASE_DIR not in file_path.parents:
        return {"error": "File not found"}

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    async def file_iterator():
        try:
            async with aiofiles.open(file_path, mode="rb") as f:
                while chunk := await f.read(1024 * 1024):
                    yield chunk
        except (ConnectionResetError, BrokenPipeError):
            return

    return StreamingResponse(file_iterator(), media_type=mime_type)
