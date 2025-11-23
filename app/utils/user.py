from typing import Optional, Any

from mysql.connector import Error as MySQLError

from app.schemas.user import UserInfo, PhoneInfo
from . import db_manager


class User:
    def __init__(self, username: str):
        self.username = username
        self.db_manager = db_manager

    def select_by_username(self) -> Optional[UserInfo]:
        """根据用户名查询用户信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT username, email, permission, phone FROM users WHERE username = %s"
                    cursor.execute(sql, (self.username,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    return UserInfo(
                        username=result['username'],
                        email=result['email'],
                        permission=result['permission'],
                        phone=str(result['phone'])
                    )
            except MySQLError as e:
                print(f"查询用户信息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue
            except Exception as e:
                print(f"未知错误: {e}")
                raise e

    def select_all(self) -> list[Any] | None:
        """查询所有用户信息（仅管理员可用）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    # 首先检查权限
                    sql = "SELECT permission FROM users WHERE username = %s"
                    cursor.execute(sql, (self.username,))
                    permission_result = cursor.fetchone()

                    if not permission_result:
                        return []

                    permission = permission_result['permission']
                    if permission not in (0, 1):
                        return []

                    # 查询所有用户
                    sql = "SELECT username, email, permission, phone FROM users"
                    cursor.execute(sql)
                    results = cursor.fetchall()

                    users = []
                    for row in results:
                        users.append(
                            UserInfo(
                                username=row['username'],
                                email=row['email'],
                                permission=row['permission'],
                                phone=str(row['phone'])
                            )
                        )
                    return users

            except MySQLError as e:
                print(f"查询所有用户失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue
            except Exception as e:
                print(f"未知错误: {e}")
                raise e

    def get_phone_info(self) -> Optional[PhoneInfo]:
        """获取用户手机信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = """
                          SELECT phone, phone_verification_code, phone_code_expire_time, phone_verified
                          FROM users
                          WHERE username = %s \
                          """
                    cursor.execute(sql, (self.username,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    if result['phone_verified'] == 0:
                        return None

                    return PhoneInfo(
                        phone=result['phone'],
                        phoneVerificationCode=result['phone_verification_code'],
                        phoneCodeExpireTime=result['phone_code_expire_time'],
                        phoneVerified=result['phone_verified']
                    )

            except MySQLError as e:
                print(f"查询手机信息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue
            except Exception as e:
                print(f"未知错误: {e}")
                raise e
