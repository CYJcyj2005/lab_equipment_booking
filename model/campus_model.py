# -*- coding: utf-8 -*-
"""校区表 DAO。"""

from db.base_model import BaseDAO


class CampusDAO(BaseDAO):
    """校区数据访问对象。"""

    def create(self, campus_name: str) -> int:
        return self.execute("INSERT INTO campus (campus_name) VALUES (?)",
                            (campus_name,))

    def get_by_id(self, cid: int) -> dict | None:
        return self.query_one("SELECT * FROM campus WHERE cid = ?", (cid,))

    def get_by_name(self, campus_name: str) -> dict | None:
        return self.query_one("SELECT * FROM campus WHERE campus_name = ?",
                              (campus_name,))

    def list_all(self) -> list:
        return self.query_all("SELECT * FROM campus ORDER BY cid")

    def delete(self, cid: int) -> None:
        self.execute("DELETE FROM campus WHERE cid = ?", (cid,))
