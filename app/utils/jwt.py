import time
import uuid
from typing import Optional, Dict

from jose import jwt
from jose.exceptions import JWTError

from .config import Config


class JWT:
    __ACCESS_EXPIRE: int = 60 * 60 * 24
    __ISS: str = "Luomuyu"
    __SECRET: bytes = Config().get_private_key().encode()
    __ALGO: str = "HS256"

    @classmethod
    def gen_access_token(cls, username: str, expire_seconds: int = None) -> str:
        now = int(time.time())
        expire = now + (expire_seconds if expire_seconds is not None else cls.__ACCESS_EXPIRE)

        payload: Dict[str, str | int] = {
            "sub": str(uuid.uuid4()),
            "name": username,
            "iss": cls.__ISS,
            "iat": now,
            "exp": expire
        }

        return jwt.encode(payload, cls.__SECRET, algorithm=cls.__ALGO)

    @classmethod
    def parse_claim(cls, token: str) -> Optional[Dict]:
        try:
            return jwt.decode(token, cls.__SECRET, algorithms=[cls.__ALGO])
        except JWTError:
            return None

    @classmethod
    def get_username(cls, token: str) -> Optional[str]:
        claims = cls.parse_claim(token)
        return claims.get("name") if claims else None

    @classmethod
    def validate_token(cls, token: str) -> bool:
        return cls.parse_claim(token) is not None
