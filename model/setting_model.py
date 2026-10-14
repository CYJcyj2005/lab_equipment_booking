# -*- coding: utf-8 -*-
"""系统参数表 DAO（键值对）。"""

from db.base_model import BaseDAO


class SettingDAO(BaseDAO):
    """系统参数数据访问对象。"""

    def get(self, key: str, default: str = "") -> str:
        row = self.query_one("SELECT svalue FROM setting WHERE skey = ?", (key,))
        return row["svalue"] if row else default

    def set(self, key: str, value) -> None:
        self.execute(
            "INSERT INTO setting (skey, svalue) VALUES (?, ?) "
            "ON CONFLICT(skey) DO UPDATE SET svalue = excluded.svalue",
            (key, str(value)))

    def all(self) -> dict:
        return {r["skey"]: r["svalue"]
                for r in self.query_all("SELECT * FROM setting")}
