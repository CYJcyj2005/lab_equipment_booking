# -*- coding: utf-8 -*-
"""站内消息表 DAO。"""

from db.base_model import BaseDAO


class MessageDAO(BaseDAO):
    """站内消息数据访问对象。"""

    def insert(self, receiver_uid: int, title: str, content: str) -> int:
        return self.execute(
            "INSERT INTO message (receiver_uid, title, content) VALUES (?, ?, ?)",
            (receiver_uid, title, content))

    def list_by_user(self, uid: int) -> list:
        return self.query_all(
            "SELECT * FROM message WHERE receiver_uid = ? ORDER BY mid DESC", (uid,))

    def mark_read(self, mid: int) -> None:
        self.execute("UPDATE message SET is_read = 1 WHERE mid = ?", (mid,))

    def mark_all_read(self, uid: int) -> None:
        self.execute("UPDATE message SET is_read = 1 WHERE receiver_uid = ?", (uid,))

    def unread_count(self, uid: int) -> int:
        row = self.query_one(
            "SELECT COUNT(*) AS c FROM message WHERE receiver_uid = ? AND is_read = 0",
            (uid,))
        return row["c"] if row else 0
