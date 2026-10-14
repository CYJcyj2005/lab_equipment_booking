# -*- coding: utf-8 -*-
"""门禁 / 电源联动 + 设备物联网实时监控（模拟）。"""

from controller.log_controller import LogController
from db.base_model import BaseDAO
from utils.constants import HW_DOOR, HW_POWER
from utils.iot_sim import random_metric


class IoTController:
    """物联联动业务逻辑（门禁/电源状态持久化 + 设备实时指标模拟）。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = BaseDAO(db_path)
        self.log = LogController(db_path)

    # ---------- 门禁 / 电源 ----------
    def _upsert(self, kind: str, ref_id: int, state: int) -> None:
        self.dao.execute(
            "INSERT INTO hardware_state (kind, ref_id, state, update_time) "
            "VALUES (?, ?, ?, datetime('now', 'localtime')) "
            "ON CONFLICT(kind, ref_id) DO UPDATE SET state = excluded.state, "
            "update_time = excluded.update_time", (kind, ref_id, state))

    def _get(self, kind: str, ref_id: int) -> int:
        row = self.dao.query_one(
            "SELECT state FROM hardware_state WHERE kind = ? AND ref_id = ?",
            (kind, ref_id))
        return row["state"] if row else 0

    def set_door(self, lab_id: int, opened: bool) -> None:
        self._upsert(HW_DOOR, lab_id, 1 if opened else 0)
        self.log.record(None, f"门禁（实验室 {lab_id}）{'开门' if opened else '关门'}")

    def set_power(self, did: int, on: bool) -> None:
        self._upsert(HW_POWER, did, 1 if on else 0)
        self.log.record(None, f"设备 {did} 电源{'通电' if on else '断电'}")

    def get_door(self, lab_id: int) -> int:
        return self._get(HW_DOOR, lab_id)

    def get_power(self, did: int) -> int:
        return self._get(HW_POWER, did)

    def list_doors(self) -> list:
        return self.dao.query_all(
            "SELECT h.ref_id AS lab_id, h.state, l.lab_name FROM hardware_state h "
            "LEFT JOIN lab l ON h.ref_id = l.lid WHERE h.kind = ? ORDER BY h.ref_id",
            (HW_DOOR,))

    def list_powers(self) -> list:
        return self.dao.query_all(
            "SELECT h.ref_id AS did, h.state, d.dev_name FROM hardware_state h "
            "LEFT JOIN device d ON h.ref_id = d.did WHERE h.kind = ? ORDER BY h.ref_id",
            (HW_POWER,))

    # ---------- 实时指标 ----------
    def refresh_metrics(self) -> None:
        """为所有设备生成一条最新实时读数。"""
        devices = self.dao.query_all("SELECT did FROM device")
        for d in devices:
            m = random_metric()
            self.dao.execute(
                "INSERT INTO device_metric (did, voltage, current, temperature, online) "
                "VALUES (?, ?, ?, ?, ?)",
                (d["did"], m["voltage"], m["current"], m["temperature"], m["online"]))

    def get_metrics(self) -> list:
        """返回各设备最新一条实时读数（联表带设备名/编号）。"""
        return self.dao.query_all(
            "SELECT dm.*, d.dev_name, d.dev_no FROM device_metric dm "
            "JOIN device d ON dm.did = d.did "
            "WHERE dm.mid IN (SELECT MAX(mid) FROM device_metric GROUP BY did) "
            "ORDER BY dm.did")
