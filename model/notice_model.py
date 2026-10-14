# -*- coding: utf-8 -*-
"""公告表 DAO。"""

from db.base_model import BaseDAO


class NoticeDAO(BaseDAO):
    """公告数据访问对象。"""

    def insert(self, title: str, content: str, publisher_uid: int) -> int:
        return self.execute(
            "INSERT INTO notice (title, content, publisher_uid) VALUES (?, ?, ?)",
            (title, content, publisher_uid))

    def get_by_id(self, nid: int) -> dict | None:
        return self.query_one("SELECT * FROM notice WHERE nid = ?", (nid,))

    def list_all(self) -> list:
        """全部公告（联表带发布者姓名），按时间倒序。"""
        return self.query_all(
            "SELECT n.*, u.real_name AS publisher_name FROM notice n "
            "JOIN user u ON n.publisher_uid = u.uid ORDER BY n.nid DESC")
