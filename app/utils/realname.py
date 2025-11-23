import re
from typing import Optional

from mysql.connector import Error as MySQLError

from app.schemas.user import RealNameInfo, UserInfo
from . import db_manager
from .phone import Phone


class RealName:
    IDCARD_PATTERN = re.compile(r"^\d{17}[\dXx]$|^\d{15}$")

    def __init__(self, user: UserInfo, real_name: Optional[str] = None, id_card: Optional[str] = None):
        self.user = user
        self.real_name = real_name
        self.id_card = id_card
        self.db_manager = db_manager

    def __idcard_validate(self) -> bool:
        """验证身份证号码格式"""
        if not self.id_card or not self.IDCARD_PATTERN.match(self.id_card):
            return False

        if len(self.id_card) == 18:
            weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
            check_digits = '10X98765432'
            try:
                total = sum(int(self.id_card[i]) * weights[i] for i in range(17))
            except ValueError:
                return False
            return self.id_card[-1].upper() == check_digits[total % 11]

        return True

    def __get_real_name_verified(self) -> bool | None:
        """检查用户是否已经完成实名认证"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT realname_verified FROM users WHERE username = %s"
                    cursor.execute(sql, (self.user.username,))
                    result = cursor.fetchone()
                    return bool(result and result['realname_verified'])
            except MySQLError as e:
                print(f"查询实名认证状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

    @staticmethod
    def __mask_real_name(real_name: Optional[str]) -> str:
        """脱敏真实姓名"""
        if not real_name:
            return ''
        name = real_name.strip()
        return name[0] + '*' * (len(name) - 1) if len(name) > 1 else name

    @staticmethod
    def __mask_id_card(id_number: Optional[str]) -> str:
        """脱敏身份证号码"""
        if not id_number:
            return ''
        id_card = id_number.strip()
        return id_card[:3] + '*' * (len(id_card) - 6) + id_card[-3:]

    def get_masked_real_name(self) -> Optional[RealNameInfo]:
        """获取脱敏的实名信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT real_name, id_card FROM users WHERE username = %s"
                    cursor.execute(sql, (self.user.username,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    return RealNameInfo(
                        realname=self.__mask_real_name(result['real_name']),
                        idcard=self.__mask_id_card(result['id_card'])
                    )
            except MySQLError as e:
                print(f"获取脱敏实名信息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

    def verify(self) -> Optional[RealNameInfo]:
        """执行实名认证"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                phone = Phone(self.user.username, self.user.phone)
                phone_verified = phone.get_phone_verified()

                idcard_valid = self.__idcard_validate()

                already_verified = self.__get_real_name_verified()

                if idcard_valid and phone_verified and not already_verified:
                    with self.db_manager.get_connection() as connection:
                        with connection.cursor(dictionary=True) as cursor:
                            sql = """
                                  UPDATE users
                                  SET real_name         = %s,
                                      id_card           = %s,
                                      realname_verified = %s
                                  WHERE username = %s \
                                  """
                            cursor.execute(sql, (
                                self.real_name,
                                self.id_card,
                                True,
                                self.user.username
                            ))
                            connection.commit()

                            return RealNameInfo(
                                realname=self.real_name,
                                idcard=self.id_card
                            )

                return None

            except MySQLError as e:
                print(f"实名认证失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

    def update_real_name_info(self, real_name: str, id_card: str) -> bool:
        """更新实名信息（不验证）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_connection() as connection:
                    with connection.cursor(dictionary=True) as cursor:
                        sql = """
                              UPDATE users
                              SET real_name = %s, \
                                  id_card   = %s
                              WHERE username = %s \
                              """
                        cursor.execute(sql, (real_name, id_card, self.user.username))
                        connection.commit()
                        return cursor.rowcount > 0
            except MySQLError as e:
                print(f"更新实名信息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue
        return False

    def get_full_real_name_info(self) -> Optional[RealNameInfo]:
        """获取完整的实名信息（管理员权限）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT real_name, id_card FROM users WHERE username = %s"
                    cursor.execute(sql, (self.user.username,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    return RealNameInfo(
                        realname=result['real_name'],
                        idcard=result['id_card'],
                    )
            except MySQLError as e:
                print(f"获取完整实名信息失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

    def check_real_name_verified(self) -> bool:
        """检查用户是否已完成实名认证"""
        return self.__get_real_name_verified()
