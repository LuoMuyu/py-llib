import hashlib
import secrets
import string


class PasswordEncryption:
    @staticmethod
    def generate_salt(length: int = 8) -> str:
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def sha256_hex(data: str, encoding: str = "utf-8") -> str:
        return hashlib.sha256(data.encode(encoding)).hexdigest()

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        first_hash = PasswordEncryption.sha256_hex(password)
        return PasswordEncryption.sha256_hex(first_hash + salt)
