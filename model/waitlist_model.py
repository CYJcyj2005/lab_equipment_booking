# -*- coding: utf-8 -*-
"""候补队列表 DAO。"""

from db.base_model import BaseDAO


class WaitlistDAO(BaseDAO):
    """候补队列数据访问对象。"""

    def insert(self, uid: int, did: int, start_time: str, end_time: str) -> int:
        return self.execute(
            "INSERT INTO waitlist (uid, did, start_time, end_time) VALUES (?, ?, ?, ?)",
            (uid, did, start_time, end_time))

    def get_by_id(self, wid: int) -> dict | None:
        return self.query_one("SELECT * FROM waitlist WHERE wid = ?", (wid,))

    def update_status(self, wid: int, status: int) -> None:
        self.execute("UPDATE waitlist SET status = ? WHERE wid = ?", (status, wid))

    def list_by_user(self, uid: int) -> list:
        return self.query_all(
            "SELECT w.*, d.dev_name, d.dev_no FROM waitlist w "
            "JOIN device d ON w.did = d.did WHERE w.uid = ? ORDER BY w.wid DESC",
            (uid,))

    def list_all(self) -> list:
        return self.query_all(
            "SELECT w.*, d.dev_name, d.dev_no, u.real_name, u.username "
            "FROM waitlist w JOIN device d ON w.did = d.did "
            "JOIN user u ON w.uid = u.uid ORDER BY w.wid")

    def get_first_waiting(self, did: int, start_time: str, end_time: str) -> dict | None:
        """返回某设备某时段最早排队（等待中）的候补记录。"""
        return self.query_one(
            "SELECT * FROM waitlist WHERE did = ? AND status = 0 "
            "AND start_time = ? AND end_time = ? ORDER BY wid LIMIT 1",
            (did, start_time, end_time))
