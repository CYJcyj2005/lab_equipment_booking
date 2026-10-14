# -*- coding: utf-8 -*-
"""信用分变动日志表 DAO。"""

from db.base_model import BaseDAO


class CreditLogDAO(BaseDAO):
    """信用分变动记录数据访问对象。"""

    def insert(self, uid: int, change: int, reason: str) -> int:
        return self.execute(
            "INSERT INTO credit_log (uid, change, reason) VALUES (?, ?, ?)",
            (uid, change, reason))

    def list_by_user(self, uid: int) -> list:
        return self.query_all(
            "SELECT * FROM credit_log WHERE uid = ? ORDER BY clid DESC", (uid,))
