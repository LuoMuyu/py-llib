import time
from contextlib import contextmanager
from typing import Optional, List

from mysql.connector import Error as MySQLError

from app.schemas.video import VideoInfo, VideoResponse
from . import db_manager


class Video:
    def __init__(self):
        self.db_manager = db_manager

    def __row_to_videoinfo(self, row: dict, url: str) -> VideoInfo:
        """将数据库行转换为 VideoInfo 对象"""
        return VideoInfo(
            url=f"{url}video/{row['video']}",
            title=row['title'],
            description=row['description'],
            like=row['like'],
            comment=row['comment']
        )

    @contextmanager
    def _execute_query(self, sql: str, params: tuple = None):
        """执行查询的上下文管理器"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.db_manager.get_cursor(dictionary=True) as cursor:
                    cursor.execute(sql, params or ())
                    yield cursor
                break
            except MySQLError as e:
                print(f"数据库查询失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)
            except Exception as e:
                print(f"未知错误: {e}")
                raise e

    def get_random_video(self, url: str, filename: Optional[str] = None) -> Optional[VideoResponse]:
        """获取随机视频"""
        try:
            total = self._get_video_count()
            if total == 0:
                return None

            video_num = 1 if total == 1 else 2
            res: List[VideoInfo] = []

            if filename and total > 1:
                current_video = self._get_video_by_filename(filename, url)
                if not current_video:
                    return None
                res.append(current_video)

                next_video = self._get_random_video_exclude(filename, url)
                if next_video:
                    res.append(next_video)
            else:
                random_videos = self._get_random_videos(video_num, url)
                if not random_videos:
                    return None
                res = random_videos

            return VideoResponse(
                video=res[0],
                next=res[1] if len(res) > 1 else None,
                msg="success",
                code=0,
                time=round(time.time() * 1000)
            )

        except Exception as e:
            print(f"获取随机视频失败: {e}")
            return None

    def _get_video_count(self) -> int:
        """获取视频总数"""
        with self._execute_query("SELECT COUNT(*) as count FROM video") as cursor:
            result = cursor.fetchone()
            return result['count'] if result else 0

    def _get_video_by_filename(self, filename: str, url: str) -> Optional[VideoInfo]:
        """根据文件名获取视频"""
        with self._execute_query("SELECT * FROM video WHERE video = %s", (filename,)) as cursor:
            row = cursor.fetchone()
            return self.__row_to_videoinfo(row, url) if row else None

    def _get_random_video_exclude(self, exclude_filename: str, url: str) -> Optional[VideoInfo]:
        """获取排除指定文件名外的随机视频"""
        with self._execute_query(
                "SELECT * FROM video WHERE video <> %s ORDER BY RAND() LIMIT 1",
                (exclude_filename,)
        ) as cursor:
            row = cursor.fetchone()
            return self.__row_to_videoinfo(row, url) if row else None

    def _get_random_videos(self, limit: int, url: str) -> List[VideoInfo]:
        """获取多个随机视频"""
        with self._execute_query(
                "SELECT * FROM video ORDER BY RAND() LIMIT %s",
                (limit,)
        ) as cursor:
            rows = cursor.fetchall()
            return [self.__row_to_videoinfo(row, url) for row in rows] if rows else []

    def get_video_by_id(self, video_id: str, url: str) -> Optional[VideoInfo]:
        """根据视频ID获取视频信息"""
        try:
            with self._execute_query("SELECT * FROM video WHERE video = %s", (video_id,)) as cursor:
                row = cursor.fetchone()
                return self.__row_to_videoinfo(row, url) if row else None
        except Exception as e:
            print(f"根据ID获取视频失败: {e}")
            return None

    def increment_like_count(self, video_id: str) -> bool:
        """增加视频点赞数"""
        try:
            with self._execute_query(
                    "UPDATE video SET `like` = `like` + 1 WHERE video = %s",
                    (video_id,)
            ) as cursor:
                return cursor.rowcount > 0
        except Exception as e:
            print(f"增加点赞数失败: {e}")
            return False

    def increment_comment_count(self, video_id: str) -> bool:
        """增加视频评论数"""
        try:
            with self._execute_query(
                    "UPDATE video SET comment = comment + 1 WHERE video = %s",
                    (video_id,)
            ) as cursor:
                return cursor.rowcount > 0
        except Exception as e:
            print(f"增加评论数失败: {e}")
            return False
