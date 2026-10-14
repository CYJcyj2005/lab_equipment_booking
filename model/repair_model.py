# -*- coding: utf-8 -*-
"""报修表 DAO。"""

from db.base_model import BaseDAO


class RepairDAO(BaseDAO):
    """报修数据访问对象。"""

    def insert(self, uid: int, did: int, content: str) -> int:
        return self.execute(
            "INSERT INTO repair (uid, did, content) VALUES (?, ?, ?)",
            (uid, did, content))

    def get_by_id(self, rid: int) -> dict | None:
        return self.query_one("SELECT * FROM repair WHERE rid = ?", (rid,))

    def update_status(self, rid: int, status: int, deal_msg: str = "") -> None:
        self.execute(
            "UPDATE repair SET status = ?, deal_msg = ?, "
            "deal_time = datetime('now', 'localtime') WHERE rid = ?",
            (status, deal_msg, rid))

    def list_by_user(self, uid: int) -> list:
        return self.query_all(
            "SELECT r.*, d.dev_name, d.dev_no FROM repair r "
            "JOIN device d ON r.did = d.did WHERE r.uid = ? ORDER BY r.rid DESC",
            (uid,))

    def list_all(self) -> list:
        return self.query_all(
            "SELECT r.*, d.dev_name, d.dev_no, u.real_name, u.username "
            "FROM repair r JOIN device d ON r.did = d.did "
            "JOIN user u ON r.uid = u.uid ORDER BY r.rid DESC")
