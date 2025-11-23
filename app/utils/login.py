from typing import Optional

from mysql.connector import Error as MySQLError

from app.schemas.user import UserInfo
from . import db_manager
from .password import PasswordEncryption
from .rsa import RSA
from .user import User


class Login:
    def __init__(self, username: str, password: str):
        self.username: str = username
        self.password: str = password
        self.db_manager = db_manager

    def login(self) -> Optional[UserInfo]:
        """用户登录验证"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT username, password, salt FROM users WHERE username = %s"
                    cursor.execute(sql, (self.username,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    is_valid = self._verify_password(result)
                    if not is_valid:
                        return None

                    user_info = User(self.username).select_by_username()
                    return user_info

            except MySQLError as e:
                print(f"登录查询失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    # self._log_login_attempt(success=False, error=str(e))
                    raise e
                continue
            except Exception as e:
                print(f"登录过程未知错误: {e}")
                # self._log_login_attempt(success=False, error=str(e))
                raise e

    def _verify_password(self, user_data: dict) -> bool:
        """验证密码"""
        try:
            db_password = user_data['password']
            db_salt = user_data['salt']

            decrypted_password = RSA().decrypt_by_private(self.password)
            if not decrypted_password:
                return False

            hashed_password = PasswordEncryption.hash_password(decrypted_password, db_salt)
            return hashed_password == db_password

        except Exception as e:
            print(f"密码验证失败: {e}")
            return False

    '''
    def _log_login_attempt(self, success: bool, error: str = None):
        """记录登录尝试"""
        try:
            with self.db_manager.get_cursor() as cursor:
                sql = """
                      INSERT INTO login_attempts (username, success, error_message, ip_address, user_agent)
                      VALUES (%s, %s, %s, %s, %s) \
                      """
                cursor.execute(sql, (self.username, success, error, None, None))
        except Exception as e:
            print(f"记录登录尝试失败: {e}")
    '''

    @classmethod
    def validate_user_credentials(cls, username: str, password: str) -> Optional[UserInfo]:
        """静态方法：验证用户凭据"""
        login = cls(username, password)
        return login.login()
