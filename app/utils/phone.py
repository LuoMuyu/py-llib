import random
import re
import time
from typing import Optional, Callable

from mysql.connector import Error as MySQLError

from . import db_manager


class Phone:
    CODE_EXPIRATION_SECONDS = 5 * 60
    PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")

    def __init__(self, username: str, phone: str, send_sms: Optional[Callable[[str, str], None]] = None):
        self.username = username
        self.phone = phone
        self.send_sms = send_sms or (lambda phone, code: print(f"发送验证码 {code} 到手机 {phone}"))
        self.db_manager = db_manager

    @staticmethod
    def __generate_code() -> str:
        return f"{random.randint(100000, 999999)}"

    def __execute_update(self, sql: str, params: tuple) -> bool:
        """执行更新操作，包含重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.rowcount > 0
            except MySQLError as e:
                print(f"数据库更新失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False
        return False

    def validate(self) -> bool:
        """验证手机号格式"""
        return bool(self.PHONE_REGEX.match(self.phone))

    def send_code(self) -> bool:
        """发送验证码"""
        if not self.validate():
            return False

        code = self.__generate_code()

        try:
            self.send_sms(self.phone, code)
        except Exception as e:
            print(f"发送短信失败: {e}")
            return False

        sql = """
              UPDATE users
              SET phone                   = %s,
                  phone_verification_code = %s,
                  phone_code_expire_time  = %s,
                  phone_verified          = %s
              WHERE username = %s \
              """
        expire_time = int(time.time()) + self.CODE_EXPIRATION_SECONDS
        return self.__execute_update(sql, (self.phone, code, expire_time, False, self.username))

    def verify_code(self, code: str) -> bool:
        """验证验证码"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = """
                          SELECT phone_verification_code, phone_code_expire_time, phone_verified
                          FROM users
                          WHERE phone = %s \
                            AND username = %s \
                          """
                    cursor.execute(sql, (self.phone, self.username))
                    result = cursor.fetchone()

                    if not result:
                        return False

                    now = int(time.time())

                    if result["phone_verified"]:
                        return False

                    if result["phone_code_expire_time"] and result["phone_code_expire_time"] < now:
                        return False

                    if code != result["phone_verification_code"]:
                        return False

                    update_sql = """
                                 UPDATE users
                                 SET phone_verification_code = %s,
                                     phone_code_expire_time  = %s,
                                     phone_verified          = %s
                                 WHERE username = %s \
                                   AND phone = %s \
                                 """
                    cursor.execute(update_sql, (None, None, True, self.username, self.phone))
                    return cursor.rowcount > 0

            except MySQLError as e:
                print(f"验证验证码失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False
        return False

    def get_phone_verified(self) -> bool:
        """获取手机验证状态"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    sql = "SELECT phone_verified FROM users WHERE username = %s"
                    cursor.execute(sql, (self.username,))
                    result = cursor.fetchone()
                    return bool(result and result["phone_verified"])
            except MySQLError as e:
                print(f"查询手机验证状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False
        return False

    def check_code_status(self) -> dict:
        """检查验证码状态"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = """
                          SELECT phone_verification_code, phone_code_expire_time, phone_verified
                          FROM users
                          WHERE username = %s \
                            AND phone = %s \
                          """
                    cursor.execute(sql, (self.username, self.phone))
                    result = cursor.fetchone()

                    if not result:
                        return {"exists": False}

                    now = int(time.time())
                    expired = result['phone_code_expire_time'] and result['phone_code_expire_time'] < now

                    return {
                        "exists": True,
                        "has_code": bool(result['phone_verification_code']),
                        "expired": expired,
                        "verified": bool(result['phone_verified']),
                        "remaining_time": max(0, result['phone_code_expire_time'] - now) if result[
                            'phone_code_expire_time'] else 0
                    }

            except MySQLError as e:
                print(f"检查验证码状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return {"exists": False, "error": str(e)}
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return {"exists": False, "error": str(e)}
        return {"exists": False, "error": "重试次数耗尽"}
