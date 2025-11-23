import base64
import textwrap
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from .config import Config


class RSA:
    def __init__(self):
        private_pem = self.wrap_pem(
            Config().get_private_key().strip(),
            "-----BEGIN PRIVATE KEY-----",
            "-----END PRIVATE KEY-----"
        )
        self.private_key: RSAPrivateKey = serialization.load_pem_private_key(private_pem, password=None)

        public_pem = self.wrap_pem(
            Config().get_public_key().strip(),
            "-----BEGIN PUBLIC KEY-----",
            "-----END PUBLIC KEY-----"
        )
        self.public_key: RSAPublicKey = serialization.load_pem_public_key(public_pem)

    @staticmethod
    def wrap_pem(b64_key: str, header: str, footer: str) -> bytes:
        b64_key = b64_key.replace("\n", "").strip()
        body = "\n".join(textwrap.wrap(b64_key, 64))
        pem = f"{header}\n{body}\n{footer}\n"
        return pem.encode("utf-8")

    def encrypt_by_public(self, data: str, encoding: str = "utf-8") -> str:
        encrypted = self.public_key.encrypt(
            data.encode(encoding),
            padding.PKCS1v15()
        )
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_by_private(self, encrypted_base64: str, encoding: str = "utf-8") -> Optional[str]:
        try:
            encrypted_bytes = base64.b64decode(encrypted_base64)
            decrypted = self.private_key.decrypt(
                encrypted_bytes,
                padding.PKCS1v15()
            )
            return decrypted.decode(encoding)
        except (ValueError, TypeError) as e:
            print(f"解密失败: {e}")
            return None
