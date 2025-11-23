import os
import secrets
import smtplib
import string
from email.header import Header
from email.mime.text import MIMEText
from typing import Optional, Dict

from mysql.connector import Error as MySQLError

from app.schemas.common import *
from app.schemas.common import ResponseNormal
from . import db_manager


class Email:
    __smtp_server: str = os.environ.get("EMAIL_HOST")
    __smtp_port: int = int(os.environ.get("EMAIL_PORT", 465))
    __sender_email: str = os.environ.get("EMAIL_USER")
    __password: str = os.environ.get("EMAIL_PASSWORD")

    def __init__(self, username: str = None, email: str = None, token: str = None):
        self.username: Optional[str] = username
        self.email: Optional[str] = email
        self.token: Optional[str] = token
        self.db_manager = db_manager

    def generate_token(self) -> str:
        """生成邮箱验证 token"""
        if not self.username or not self.email:
            raise ValueError("用户名和邮箱不能为空")

        chars = string.ascii_uppercase + string.digits
        self.token = ''.join(secrets.choice(chars) for _ in range(32))
        return self.token

    def save_token_to_db(self) -> bool:
        """将 token 保存到数据库"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    sql = """
                          UPDATE users
                          SET email_verification_token = %s, \
                              email_verified           = %s
                          WHERE username = %s \
                          """
                    cursor.execute(sql, (self.token, 0, self.username))
                    return True

            except MySQLError as e:
                print(f"保存 token 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                continue
            except Exception as e:
                print(f"未知错误: {e}")
                return False
        return False

    def send_email(self) -> bool:
        """发送验证邮件"""
        if not self.token:
            raise ValueError("Token 未生成，请先调用 generate_token()")

        subject = "邮箱验证 - 欢迎注册"
        link = f"http://localhost:3000/register?token={self.token}"
        html_content = (
            f"<h2>您好，{self.username}</h2>"
            f"<p>请点击以下链接完成邮箱验证：</p>"
            f"<a href='{link}'>{link}</a>"
            f"<p>如果无法点击，请复制链接到浏览器打开。</p>"
            f"<p>此链接有效期为24小时。</p>"
        )

        message = MIMEText(html_content, "html", "utf-8")
        message["From"] = f"图书管理系统 <{self.__sender_email}>"
        message["To"] = self.email
        message["Subject"] = Header(subject, "utf-8")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP_SSL(self.__smtp_server, self.__smtp_port) as server:
                    server.login(self.__sender_email, self.__password)
                    server.sendmail(self.__sender_email, self.email, message.as_string())
                    print(f"邮件发送成功！收件人: {self.email}")
                    return True

            except smtplib.SMTPException as e:
                print(f"邮件发送失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                continue
            except Exception as e:
                print(f"邮件发送未知错误: {e}")
                return False
        return False

    def send_verification_email(self) -> ResponseNormal:
        """发送验证邮件的完整流程"""
        try:
            self.generate_token()

            if not self.save_token_to_db():
                return ResponseNormal(msg="保存验证信息失败", code=1)

            if self.send_email():
                return ResponseNormal(msg="验证邮件发送成功")
            else:
                return ResponseNormal(msg="邮件发送失败", code=1)

        except Exception as e:
            print(f"发送验证邮件异常: {e}")
            return ResponseNormal(msg="系统错误，请稍后重试", code=1)

    def resend_email(self) -> ResponseNormal | None:
        """重新发送验证邮件"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT email_verification_token, email FROM users WHERE username=%s"
                    cursor.execute(sql, (self.username,))
                    result = cursor.fetchone()

                    if not result:
                        return ResponseNormal(msg="用户不存在", code=1)

                    if not result['email_verification_token'] or not result['email']:
                        return ResponseNormal(msg="用户信息不完整", code=1)

                    self.token = result['email_verification_token']
                    self.email = result['email']

                    if self.send_email():
                        return ResponseNormal(msg="邮件发送成功")
                    else:
                        return ResponseNormal(msg="邮件发送失败", code=1)

            except MySQLError as e:
                print(f"重新发送邮件失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return ResponseNormal(msg="数据库错误", code=1)
                continue
            except Exception as e:
                print(f"重新发送邮件未知错误: {e}")
                return ResponseNormal(msg="系统错误", code=1)

    def verify_email(self, token: str) -> Optional[Dict[str, str]]:
        """验证邮箱 token"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = """
                          SELECT username, email, email_verified
                          FROM users
                          WHERE email_verification_token = %s \
                          """
                    cursor.execute(sql, (token,))
                    result = cursor.fetchone()

                    if not result:
                        return None

                    username = result['username']
                    email = result['email']
                    email_verified = result['email_verified']

                    if email_verified == 1:
                        return None

                    update_sql = """
                                 UPDATE users
                                 SET email_verification_token = NULL,
                                     email_verified           = %s,
                                     permission               = %s
                                 WHERE username = %s \
                                 """
                    cursor.execute(update_sql, (1, 3, username))

                    return {"username": username, "email": email}

            except MySQLError as e:
                print(f"邮箱验证失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                continue
            except Exception as e:
                print(f"邮箱验证未知错误: {e}")
                return None

    def check_email_verified(self, username: str) -> bool | None | Any:
        """检查邮箱是否已验证"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT email_verified FROM users WHERE username = %s"
                    cursor.execute(sql, (username,))
                    result = cursor.fetchone()

                    return result and result['email_verified'] == 1

            except MySQLError as e:
                print(f"检查邮箱验证状态失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                continue
            except Exception as e:
                print(f"检查邮箱验证状态未知错误: {e}")
                return False
