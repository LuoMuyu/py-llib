from fastapi import APIRouter

from app.schemas.common import RSAResponse
from app.utils.config import Config

router = APIRouter()


@router.get("/publicKey")
async def get_public_key() -> RSAResponse:
    return RSAResponse(publicKey=Config().get_public_key())
