# -*- coding: utf-8 -*-
"""签到记录表 DAO。"""

from db.base_model import BaseDAO


class SignDAO(BaseDAO):
    """签到记录数据访问对象。"""

    def insert(self, uid: int, aid: int | None, did: int,
               method: str, result: int = 1) -> int:
        return self.execute(
            "INSERT INTO sign_in (uid, aid, did, method, result) VALUES (?, ?, ?, ?, ?)",
            (uid, aid, did, method, result))

    def list_all(self) -> list:
        return self.query_all(
            "SELECT s.*, u.real_name, d.dev_name FROM sign_in s "
            "JOIN user u ON s.uid = u.uid JOIN device d ON s.did = d.did "
            "ORDER BY s.sid DESC")

    def list_by_user(self, uid: int) -> list:
        return self.query_all(
            "SELECT s.*, d.dev_name FROM sign_in s JOIN device d ON s.did = d.did "
            "WHERE s.uid = ? ORDER BY s.sid DESC", (uid,))

    def has_signed(self, aid: int) -> bool:
        row = self.query_one("SELECT sid FROM sign_in WHERE aid = ?", (aid,))
        return row is not None
