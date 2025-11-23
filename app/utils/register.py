import re
import time
from typing import Optional, Any

from mysql.connector import Error as MySQLError

from app.schemas.common import ResponseNormal
from . import db_manager
from .email import Email
from .password import PasswordEncryption
from .rsa import RSA
from .user import User


class Register:
    EMAIL_REGEX = re.compile(r"^[\w.-]+@[\w.-]+\.\w+$")

    def __init__(self, username: str, password: str, email: str):
        self.username = username
        self.password = password
        self.email = email
        self.db_manager = db_manager

    def validate_input(self) -> Optional[ResponseNormal]:
        """验证输入数据"""
        if not self.username or len(self.username) < 3:
            return ResponseNormal(msg="用户名至少3个字符", code=1)

        if not self.password or len(self.password) < 6:
            return ResponseNormal(msg="密码至少6个字符", code=1)

        if not self.EMAIL_REGEX.fullmatch(self.email):
            return ResponseNormal(msg="邮箱格式错误", code=1)

        return None

    def check_existing_user(self) -> Optional[ResponseNormal]:
        """检查用户是否已存在"""
        try:
            user = User(self.username)
            if user.select_by_username():
                return ResponseNormal(msg="用户名已存在", code=1)

            # 也可以检查邮箱是否已被使用
            if self._is_email_registered():
                return ResponseNormal(msg="邮箱已被注册", code=1)

            return None
        except Exception as e:
            print(f"检查用户存在性失败: {e}")
            return ResponseNormal(msg="系统错误，请稍后重试", code=1)

    def _is_email_registered(self) -> bool:
        """检查邮箱是否已被注册"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT username FROM users WHERE email = %s"
                    cursor.execute(sql, (self.email,))
                    result = cursor.fetchone()
                    return result is not None
            except MySQLError as e:
                print(f"检查邮箱注册状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return True
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return True
        return True

    def create_user(self) -> bool | None:
        """创建用户"""
        salt = PasswordEncryption.generate_salt()
        try:
            decrypted_password = RSA().decrypt_by_private(self.password)
        except Exception as e:
            print(f"密码解密失败: {e}")
            return False

        hashed_password = PasswordEncryption.hash_password(decrypted_password, salt)

        email_util = Email(self.username, self.email)
        token = email_util.generate_token()
        email_util.token = token

        permission = 4
        create_time = round(time.time() * 1000)

        sql = """
              INSERT INTO users (username, password, salt, email, permission, create_time, \
                                 email_verification_token, email_verified, phone_verified, realname_verified) \
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
              """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute(sql, (
                        self.username, hashed_password, salt, self.email,
                        permission, create_time, token, 0, 0, 0
                    ))
                    email_sent = email_util.send_email()
                    if not email_sent:
                        print("警告：验证邮件发送失败")

                    return True

            except MySQLError as e:
                print(f"创建用户失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if e.errno == 1062:
                    return False

                if attempt == max_retries - 1:
                    return False
                time.sleep(1)

            except Exception as e:
                print(f"创建用户时发生未知错误: {e}")
                return False

    def register(self) -> ResponseNormal:
        """用户注册主方法"""
        try:
            validation_error = self.validate_input()
            if validation_error:
                return validation_error

            existing_error = self.check_existing_user()
            if existing_error:
                return existing_error

            if self.create_user():
                return ResponseNormal(
                    msg="注册成功，请查收验证邮件完成账号激活",
                    code=0
                )
            else:
                return ResponseNormal(
                    msg="注册失败，请稍后重试",
                    code=1
                )

        except Exception as e:
            print(f"注册过程发生异常: {e}")
            return ResponseNormal(
                msg="系统错误，请稍后重试",
                code=1
            )
