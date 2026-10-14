# -*- coding: utf-8 -*-
"""预约表 DAO。"""

from db.base_model import BaseDAO
from utils.constants import AUDIT_PENDING, AUDIT_APPROVED


class AppointmentDAO(BaseDAO):
    """预约数据访问对象。"""

    def insert(self, uid: int, did: int, start_time: str, end_time: str,
               appointment_type: str = "instant", tutor_uid: int | None = None,
               approve_stage: int = 2, recurrence_group: str = "") -> int:
        return self.execute(
            "INSERT INTO appointment (uid, did, start_time, end_time, "
            "appointment_type, tutor_uid, approve_stage, recurrence_group) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, did, start_time, end_time, appointment_type, tutor_uid,
             approve_stage, recurrence_group))

    def get_by_id(self, aid: int) -> dict | None:
        return self.query_one("SELECT * FROM appointment WHERE aid = ?", (aid,))

    def update_audit(self, aid: int, audit_status: int, audit_msg: str = "") -> None:
        self.execute("UPDATE appointment SET audit_status = ?, audit_msg = ? WHERE aid = ?",
                     (audit_status, audit_msg, aid))

    def update_status(self, aid: int, audit_status: int) -> None:
        self.execute("UPDATE appointment SET audit_status = ? WHERE aid = ?",
                     (audit_status, aid))

    def get_valid_time_range_by_device(self, did: int) -> list:
        """返回某设备「占用中」的时段列表（待审核 + 已通过）。"""
        rows = self.query_all(
            "SELECT start_time, end_time FROM appointment "
            "WHERE did = ? AND audit_status IN (?, ?)",
            (did, AUDIT_PENDING, AUDIT_APPROVED))
        return [(r["start_time"], r["end_time"]) for r in rows]

    def count_overlap(self, did: int, start: str, end: str,
                      exclude_aid: int | None = None) -> int:
        """统计与 [start, end) 重叠的「待审核+已通过」预约数量（用于多数量并发）。"""
        sql = ("SELECT COUNT(*) AS c FROM appointment "
               "WHERE did = ? AND audit_status IN (?, ?) AND start_time < ? AND end_time > ?")
        params: list = [did, AUDIT_PENDING, AUDIT_APPROVED, end, start]
        if exclude_aid is not None:
            sql += " AND aid != ?"
            params.append(exclude_aid)
        row = self.query_one(sql, tuple(params))
        return row["c"] if row else 0

    def list_by_user(self, uid: int) -> list:
        """某用户的全部预约（联表带设备名/编号）。"""
        return self.query_all(
            "SELECT a.*, d.dev_name, d.dev_no FROM appointment a "
            "JOIN device d ON a.did = d.did WHERE a.uid = ? ORDER BY a.aid DESC",
            (uid,))

    def list_by_status(self, audit_status: int) -> list:
        """按审核状态列出预约（联表带设备/用户信息）。"""
        return self.query_all(
            "SELECT a.*, d.dev_name, d.dev_no, u.real_name, u.username "
            "FROM appointment a JOIN device d ON a.did = d.did "
            "JOIN user u ON a.uid = u.uid WHERE a.audit_status = ? "
            "ORDER BY a.aid DESC", (audit_status,))

    def list_all(self) -> list:
        """全部预约（联表带设备/用户信息）。"""
        return self.query_all(
            "SELECT a.*, d.dev_name, d.dev_no, u.real_name, u.username "
            "FROM appointment a JOIN device d ON a.did = d.did "
            "JOIN user u ON a.uid = u.uid ORDER BY a.aid DESC")

    def count_no_show_by_user(self, uid: int) -> int:
        row = self.query_one(
            "SELECT COUNT(*) AS c FROM appointment WHERE uid = ? AND audit_status = 5",
            (uid,))
        return row["c"] if row else 0
