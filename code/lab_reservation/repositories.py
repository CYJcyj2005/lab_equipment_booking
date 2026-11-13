# -*- coding: utf-8 -*-
"""内存数据仓库。

采用「仓库模式（Repository Pattern）」将数据存取与业务逻辑解耦，
演示阶段使用内存字典存储；实际工程中可将本类替换为基于
MySQL / SQLAlchemy 的实现，业务层（services）无需改动。

对应《软件需求规格说明书》6.1 节的各数据表。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import Equipment, Lab, Reservation, UsageRecord, User


class InMemoryRepository:
    """统一内存仓库，管理用户 / 实验室 / 设备 / 预约单 / 使用记录五类数据。"""

    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.labs: Dict[str, Lab] = {}
        self.equipments: Dict[str, Equipment] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.usage_records: Dict[str, UsageRecord] = {}

    # ---- 用户 ----
    def add_user(self, user: User) -> None:
        self.users[user.user_id] = user

    def find_user_by_sid(self, sid: str) -> Optional[User]:
        for u in self.users.values():
            if u.sid == sid:
                return u
        return None

    # ---- 实验室 ----
    def add_lab(self, lab: Lab) -> None:
        self.labs[lab.lab_id] = lab

    # ---- 设备 ----
    def add_equipment(self, eq: Equipment) -> None:
        self.equipments[eq.equip_id] = eq

    def find_equipment(self, equip_id: str) -> Optional[Equipment]:
        return self.equipments.get(equip_id)

    def list_equipments(self) -> List[Equipment]:
        return list(self.equipments.values())

    # ---- 预约单 ----
    def add_reservation(self, r: Reservation) -> None:
        self.reservations[r.reserve_id] = r

    def find_reservation(self, reserve_id: str) -> Optional[Reservation]:
        return self.reservations.get(reserve_id)

    def list_reservations(self) -> List[Reservation]:
        return list(self.reservations.values())

    # ---- 使用记录 ----
    def add_usage_record(self, rec: UsageRecord) -> None:
        self.usage_records[rec.record_id] = rec
