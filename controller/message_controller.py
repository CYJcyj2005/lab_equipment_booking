# -*- coding: utf-8 -*-
"""站内消息控制器。"""

from model.message_model import MessageDAO


class MessageController:
    """站内消息的发送、查询、已读标记。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = MessageDAO(db_path)

    def send_message(self, receiver_uid: int, title: str, content: str) -> tuple:
        """给指定用户发送一条站内消息，返回 (是否成功, mid)。"""
        mid = self.dao.insert(receiver_uid, title, content)
        return mid > 0, mid

    def list_by_user(self, uid: int) -> list:
        return self.dao.list_by_user(uid)

    def mark_read(self, mid: int) -> None:
        self.dao.mark_read(mid)

    def mark_all_read(self, uid: int) -> None:
        self.dao.mark_all_read(uid)

    def unread_count(self, uid: int) -> int:
        return self.dao.unread_count(uid)
