import time

from mysql.connector import Error as MySQLError

from app.schemas.pic import PicInfo, PicResponse
from . import db_manager


class Pic:
    def __init__(self):
        self.db_manager = db_manager

    def get_pic_list(self, url: str) -> PicResponse:
        """获取随机图片列表"""
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=False) as cursor:
                    sql = "SELECT title, pic FROM pic ORDER BY RAND() LIMIT 5"
                    cursor.execute(sql)
                    rows = cursor.fetchall()

                    if not rows:
                        return self._create_empty_response()

                    pics = []
                    for row in rows:
                        title, pic = row
                        pics.append(
                            PicInfo(
                                title=title,
                                url=f"{url}pic/{pic}",
                            )
                        )

                    return PicResponse(
                        data=pics,
                        msg="success",
                        code=0,
                        time=round(time.time() * 1000)
                    )

            except MySQLError as e:
                last_exception = e
                print(f"获取图片列表失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if self._is_connection_error(e):
                    time.sleep(1)
                    continue
                else:
                    break

            except Exception as e:
                last_exception = e
                print(f"获取图片列表未知错误: {e}")
                break

        return self._create_error_response(last_exception)

    def get_pic_list_with_fallback(self, url: str) -> PicResponse:
        """带降级策略的获取图片列表方法"""
        try:
            return self.get_pic_list(url)
        except Exception as e:
            print(f"图片获取完全失败，使用空数据降级: {e}")
            return self._create_empty_response()

    def _is_connection_error(self, error: MySQLError) -> bool:
        """判断是否为连接错误"""
        connection_errors = [
            2003,  # Can't connect to MySQL server
            2006,  # MySQL server has gone away
            2013,  # Lost connection to MySQL server
            2026,  # SSL connection error
        ]
        return hasattr(error, 'errno') and error.errno in connection_errors

    def _create_empty_response(self) -> PicResponse:
        """创建空数据响应"""
        return PicResponse(
            data=[],
            msg="未找到图片数据",
            code=404,
            time=round(time.time() * 1000)
        )

    def _create_error_response(self, error: Exception) -> PicResponse:
        """创建错误响应"""
        return PicResponse(
            data=[],
            msg=f"获取图片失败: {str(error)}",
            code=500,
            time=round(time.time() * 1000)
        )

    def get_pic_count(self) -> int:
        """获取图片总数（用于监控）"""
        try:
            with self.db_manager.get_cursor() as cursor:
                sql = "SELECT COUNT(*) as count FROM pic"
                cursor.execute(sql)
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"获取图片总数失败: {e}")
            return 0
