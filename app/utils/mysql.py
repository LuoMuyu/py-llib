from mysql.connector import pooling
from mysql.connector import Error as MySQLError
from contextlib import contextmanager
from typing import Generator
import os


class DatabaseManager:
    def __init__(self):
        self.connection_pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="user_pool",
                pool_size=10,
                pool_reset_session=True,
                host=os.getenv('MYSQL_HOST'),
                port=os.getenv('MYSQL_PORT'),
                database=os.getenv('MYSQL_DB'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('MYSQL_PASSWORD'),
                autocommit=True,
                connect_timeout=30,
                connection_timeout=30,
                buffered=True
            )
            print("数据库连接池初始化成功")
        except MySQLError as e:
            print(f"数据库连接池初始化失败: {e}")
            raise

    @contextmanager
    def get_connection(self) -> Generator:
        """获取数据库连接的上下文管理器"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except MySQLError as e:
            print(f"获取数据库连接失败: {e}")
            raise
        finally:
            if connection:
                connection.close()

    @contextmanager
    def get_cursor(self, dictionary: bool = True) -> Generator:
        """获取游标的上下文管理器"""
        with self.get_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor(dictionary=dictionary)
                yield cursor
            finally:
                if cursor:
                    cursor.close()
