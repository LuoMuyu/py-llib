from typing import Optional, List

from mysql.connector import Error as MySQLError

from app.schemas.book import *
from app.schemas.book import BookDataBase, BorrowInfo
from . import db_manager


class Book:
    def __init__(self, book_id: int = None, title: str = None, author: str = None,
                 description: str = None, pic: str = None, book_type: str = None,
                 price: int = None, count: int = None):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.description = description
        self.pic = pic
        self.type = book_type
        self.price = price
        self.count = count
        self.db_manager = db_manager

    def get_list(self) -> Optional[List[BookDataBase]]:
        """获取图书列表"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = "SELECT * FROM books"

                    cursor.execute(sql)
                    results = cursor.fetchall()

                    if not results:
                        print("没有找到图书数据")
                        return None

                    books = []
                    for i, row in enumerate(results):
                        try:
                            book = BookDataBase(
                                id=row['id'],
                                author=row['author'],
                                book_id=row['book_id'],
                                borrow_count=row['borrow_count'],
                                count=row['count'],
                                description=row['description'],
                                pic=row['pic'],
                                price=row['price'],
                                title=row['title'],
                                type=row['type']
                            )
                            books.append(book)
                        except KeyError as e:
                            continue
                        except Exception as e:
                            continue
                    return books

            except MySQLError as e:
                print(f"获取图书列表数据库错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
            except Exception as e:
                print(f"获取图书列表未知错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)

    def add_book(self, books: list[AddBookRequest]) -> bool | None:
        """添加图书"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("SELECT MAX(book_id) FROM books")
                    result = cursor.fetchone()
                    current_max_id = result[0] if result[0] is not None else 100000

                    for book in books:
                        book_id = current_max_id + 1
                        current_max_id = book_id

                        sql = """
                              INSERT INTO books
                              (book_id, title, author, description, pic, type, price, count, borrow_count)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0) \
                              """
                        cursor.execute(sql, (
                            book_id, book.title, book.author, book.description,
                            book.pic, book.type, book.price, book.count
                        ))

                    return True

            except MySQLError as e:
                print(f"添加图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False

    def update_book(self) -> bool | None:
        """更新图书信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    sql = """
                          UPDATE books \
                          SET title=%s, \
                              author=%s, \
                              description=%s, \
                              pic=%s, \
                              type=%s, \
                              price=%s, \
                              count=%s \
                          WHERE book_id = %s \
                          """
                    cursor.execute(sql, (
                        self.title, self.author, self.description, self.pic,
                        self.type, self.price, self.count, self.book_id
                    ))

                    if cursor.rowcount == 0:
                        return False

                    return True

            except MySQLError as e:
                print(f"更新图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False

    def del_book(self) -> bool | None:
        """删除图书"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("SELECT borrow_count FROM books WHERE book_id=%s", (self.book_id,))
                    result = cursor.fetchone()
                    if not result:
                        return False

                    borrow_count = result[0]
                    if borrow_count > 0:
                        return False

                    cursor.execute("DELETE FROM books WHERE book_id=%s", (self.book_id,))

                    if cursor.rowcount == 0:
                        return False

                    return True

            except MySQLError as e:
                print(f"删除图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False

    def borrow_book(self, borrow_long: int, username: str) -> bool | None:
        """借阅图书"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with (self.db_manager.get_cursor() as cursor):
                    cursor.execute("SELECT borrow_count, count FROM books WHERE book_id=%s", (self.book_id,))
                    result = cursor.fetchone()
                    print( result)
                    if not result:
                        return False

                    borrow_count = result["borrow_count"]
                    total_count = result["count"]
                    if total_count - borrow_count <= 0:
                        return False

                    cursor.execute("UPDATE books SET borrow_count=%s WHERE book_id=%s",
                                   (borrow_count + 1, self.book_id))

                    borrow_time = int(time.time() * 1000)
                    cursor.execute("""
                                   INSERT INTO circulate
                                       (book_id, borrow_long, borrow_time, username, is_time_out, is_return)
                                   VALUES (%s, %s, %s, %s, 0, 0)
                                   """, (self.book_id, borrow_long, borrow_time, username))

                    return True

            except MySQLError as e:
                print(f"借阅图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False

    def return_book(self, username: str) -> bool | None:
        """归还图书"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("""
                                   SELECT id, borrow_time, borrow_long
                                   FROM circulate
                                   WHERE book_id = %s
                                     AND username = %s
                                     AND is_return = 0
                                   ORDER BY borrow_time DESC
                                   LIMIT 1
                                   """, (self.book_id, username))

                    record = cursor.fetchone()
                    if not record:
                        return False

                    record_id, borrow_time, borrow_long = record
                    return_time = int(time.time() * 1000)

                    is_time_out = 1 if return_time - borrow_time > borrow_long * 24 * 60 * 60 * 1000 else 0

                    cursor.execute("""
                                   UPDATE circulate
                                   SET return_time=%s,
                                       is_return=1,
                                       is_time_out=%s
                                   WHERE id = %s
                                   """, (return_time, is_time_out, record_id))

                    cursor.execute("UPDATE books SET borrow_count=borrow_count-1 WHERE book_id=%s",
                                   (self.book_id,))

                    return True

            except MySQLError as e:
                print(f"归还图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                return False

    def get_circulate_list(self, username: str, permission: int) -> list[BorrowInfo] | None:
        """获取借阅记录"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    if permission > 1:
                        sql = "SELECT * FROM circulate WHERE username=%s ORDER BY borrow_time DESC"
                        cursor.execute(sql, (username,))
                    else:
                        sql = "SELECT * FROM circulate ORDER BY borrow_time DESC"
                        cursor.execute(sql)

                    results = cursor.fetchall()
                    if not results:
                        return None

                    return [
                        BorrowInfo(
                            id=row['id'],
                            bookId=row['book_id'],
                            borrowLong=row['borrow_long'],
                            borrowTime=row['borrow_time'],
                            isReturn=bool(row['is_return']),
                            isTimeOut=bool(row['is_time_out']),
                            returnTime=row['return_time'] if row['return_time'] else 0,
                            username=row['username']
                        )
                        for row in results
                    ]

            except MySQLError as e:
                print(f"获取借阅记录失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
            except Exception as e:
                print(f"获取借阅记录未知错误: {e}")
                return None

    def search_books(self, keyword: str) -> Optional[List[BookDataBase]]:
        """搜索图书"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 使用字典游标
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    sql = """
                          SELECT * \
                          FROM books
                          WHERE title LIKE %s
                             OR author LIKE %s
                             OR description LIKE %s \
                          """
                    search_pattern = f"%{keyword}%"
                    cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
                    results = cursor.fetchall()

                    if not results:
                        return None

                    return [
                        BookDataBase(
                            id=row['id'],
                            author=row['author'],
                            book_id=row['book_id'],
                            borrow_count=row['borrow_count'],
                            count=row['count'],
                            description=row['description'],
                            pic=row['pic'],
                            price=row['price'],
                            title=row['title'],
                            type=row['type']
                        )
                        for row in results
                    ]

            except MySQLError as e:
                print(f"搜索图书失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
            except Exception as e:
                print(f"搜索图书未知错误: {e}")
                return None