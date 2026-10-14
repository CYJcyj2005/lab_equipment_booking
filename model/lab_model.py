# -*- coding: utf-8 -*-
"""实验室表 DAO。"""

from db.base_model import BaseDAO


class LabDAO(BaseDAO):
    """实验室数据访问对象。"""

    def create(self, lab_name: str, location: str = "", open_time: str = "",
               remark: str = "", campus_id: int | None = None) -> int:
        return self.execute(
            "INSERT INTO lab (lab_name, location, open_time, remark, campus_id) "
            "VALUES (?, ?, ?, ?, ?)", (lab_name, location, open_time, remark, campus_id))

    def get_by_id(self, lid: int) -> dict | None:
        return self.query_one(
            "SELECT l.*, c.campus_name FROM lab l LEFT JOIN campus c ON l.campus_id = c.cid "
            "WHERE l.lid = ?", (lid,))

    def list_all(self, campus_id: int | None = None) -> list:
        sql = ("SELECT l.*, c.campus_name FROM lab l "
               "LEFT JOIN campus c ON l.campus_id = c.cid WHERE 1=1")
        params: list = []
        if campus_id is not None:
            sql += " AND l.campus_id = ?"
            params.append(campus_id)
        sql += " ORDER BY l.lid"
        return self.query_all(sql, tuple(params))

    def update(self, lid: int, **fields) -> None:
        allowed = {"lab_name", "location", "open_time", "remark", "campus_id"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        self.execute(f"UPDATE lab SET {set_clause} WHERE lid = ?",
                     (*updates.values(), lid))
