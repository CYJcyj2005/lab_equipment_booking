# -*- coding: utf-8 -*-
"""业务逻辑层（服务层）。

对应《软件需求规格说明书》第 3 章的功能需求，实现：
    - ReservationService  预约 / 审核 / 使用登记（核心模块）
    - EquipmentService    设备台账管理
    - UserService         用户注册 / 登录

所有业务规则（冲突检测、状态机、权限校验）均在本层实现。
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import List, Optional

from .exceptions import (
    ConflictError, NotFoundError, PermissionError, StateError, ValidationError,
)
from .models import (
    Equipment, EquipmentStatus, Reservation, ReservationStatus, Role,
    UsageRecord, User,
)
from .repositories import InMemoryRepository

# 可预约的预约单状态（视为「占用」）
_ACTIVE_STATUSES = (ReservationStatus.PENDING, ReservationStatus.APPROVED)


def _parse_slot(slot: str) -> tuple[int, int]:
    """将 "HH:MM-HH:MM" 解析为 (开始分钟数, 结束分钟数)。"""
    start, end = slot.split("-")

    def _to_min(s: str) -> int:
        h, m = s.strip().split(":")
        return int(h) * 60 + int(m)

    return _to_min(start), _to_min(end)


def slots_overlap(slot_a: str, slot_b: str) -> bool:
    """判断两个时段是否重叠（开区间，首尾相接不算冲突）。"""
    a1, a2 = _parse_slot(slot_a)
    b1, b2 = _parse_slot(slot_b)
    return a1 < b2 and b1 < a2


def _hash_password(raw: str) -> str:
    """密码哈希（演示用 SHA-256，实际工程建议使用 bcrypt + 盐）。"""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ReservationService:
    """预约与审核服务 —— 系统核心模块。"""

    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo
        self._seq = 0

    # ---------- 内部工具 ----------
    def _next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq:04d}"

    def _get_reservation(self, reserve_id: str) -> Reservation:
        r = self.repo.find_reservation(reserve_id)
        if r is None:
            raise NotFoundError(f"预约单不存在：{reserve_id}")
        return r

    def _find_usage(self, reserve_id: str) -> Optional[UsageRecord]:
        for rec in self.repo.usage_records.values():
            if rec.reserve_id == reserve_id:
                return rec
        return None

    # ---------- 预约 ----------
    def check_conflict(self, equip_id: str, reserve_date: date,
                       time_slot: str) -> List[Reservation]:
        """检测同一设备、同一日期、重叠时段的有效预约。"""
        return [
            r for r in self.repo.list_reservations()
            if r.equip_id == equip_id
            and r.reserve_date == reserve_date
            and r.status in _ACTIVE_STATUSES
            and slots_overlap(r.time_slot, time_slot)
        ]

    def submit(self, user: User, equip_id: str, reserve_date: date,
               time_slot: str, purpose: str) -> Reservation:
        """提交预约申请，生成「待审核」预约单。"""
        if user.status != "正常":
            raise PermissionError("账号已被禁用，无法预约")
        eq = self.repo.find_equipment(equip_id)
        if eq is None:
            raise NotFoundError(f"设备不存在：{equip_id}")
        if eq.status != EquipmentStatus.AVAILABLE:
            raise ValidationError(f"设备当前状态为「{eq.status.value}」，不可预约")
        if not purpose.strip():
            raise ValidationError("预约用途不能为空")

        # 规则：同一用户同一时段只能持有一张有效预约单
        for r in self.repo.list_reservations():
            if (r.user_id == user.user_id and r.reserve_date == reserve_date
                    and r.status in _ACTIVE_STATUSES
                    and slots_overlap(r.time_slot, time_slot)):
                raise ConflictError("您在该时段已有其他预约，请先取消后再预约")

        # 规则：设备时段冲突检测
        if self.check_conflict(equip_id, reserve_date, time_slot):
            raise ConflictError("该设备在所选时段已被预约，请选择其他时段")

        reservation = Reservation(
            reserve_id=self._next_id("R"),
            user_id=user.user_id,
            equip_id=equip_id,
            reserve_date=reserve_date,
            time_slot=time_slot,
            purpose=purpose,
        )
        self.repo.add_reservation(reservation)
        return reservation

    # ---------- 审核 ----------
    def approve(self, reserve_id: str, approver: User) -> Reservation:
        """审核通过，需复核时段冲突。"""
        r = self._get_reservation(reserve_id)
        if r.status != ReservationStatus.PENDING:
            raise StateError(f"当前状态「{r.status.value}」不可审核")
        conflicts = [
            c for c in self.check_conflict(r.equip_id, r.reserve_date, r.time_slot)
            if c.reserve_id != r.reserve_id
        ]
        if conflicts:
            raise ConflictError("审核时发现时段冲突，请先处理冲突预约")
        r.status = ReservationStatus.APPROVED
        r.approver = approver.user_id
        r.approve_time = datetime.now()
        return r

    def reject(self, reserve_id: str, approver: User, reason: str) -> Reservation:
        """审核驳回，必须填写驳回原因。"""
        r = self._get_reservation(reserve_id)
        if r.status != ReservationStatus.PENDING:
            raise StateError(f"当前状态「{r.status.value}」不可审核")
        if not reason.strip():
            raise ValidationError("驳回必须填写驳回原因")
        r.status = ReservationStatus.REJECTED
        r.approver = approver.user_id
        r.approve_time = datetime.now()
        r.opinion = reason.strip()
        return r

    # ---------- 取消 ----------
    def cancel(self, reserve_id: str, operator: User) -> Reservation:
        """取消预约。普通用户只能取消本人预约，管理员可取消任意预约。"""
        r = self._get_reservation(reserve_id)
        if r.status not in _ACTIVE_STATUSES:
            raise StateError(f"当前状态「{r.status.value}」不可取消")
        is_owner = r.user_id == operator.user_id
        is_admin = operator.role in (Role.LAB_ADMIN, Role.SYS_ADMIN)
        if not (is_owner or is_admin):
            raise PermissionError("只能取消本人预约")
        r.status = ReservationStatus.CANCELLED
        return r

    # ---------- 使用登记 ----------
    def sign_in(self, reserve_id: str, user: User) -> UsageRecord:
        """签到开始使用，设备状态置为「使用中」。"""
        r = self._get_reservation(reserve_id)
        if r.status != ReservationStatus.APPROVED:
            raise StateError("仅「已通过」的预约可签到")
        if r.user_id != user.user_id:
            raise PermissionError("只能为本人预约签到")
        existing = self._find_usage(reserve_id)
        if existing is not None:
            raise StateError("该预约已签到，请勿重复签到")
        rec = UsageRecord(
            record_id=self._next_id("U"),
            reserve_id=reserve_id,
            equip_id=r.equip_id,
            user_id=user.user_id,
            sign_in_time=datetime.now(),
        )
        eq = self.repo.find_equipment(r.equip_id)
        if eq is not None:
            eq.status = EquipmentStatus.IN_USE
        self.repo.add_usage_record(rec)
        return rec

    def sign_out(self, reserve_id: str, user: User) -> UsageRecord:
        """签退归还，设备状态恢复为「可用」，预约单置为「已完成」。"""
        r = self._get_reservation(reserve_id)
        if r.user_id != user.user_id:
            raise PermissionError("只能为本人预约签退")
        rec = self._find_usage(reserve_id)
        if rec is None or rec.sign_in_time is None:
            raise StateError("尚未签到，无法签退")
        if rec.sign_out_time is not None:
            raise StateError("该预约已签退")
        rec.sign_out_time = datetime.now()
        eq = self.repo.find_equipment(r.equip_id)
        if eq is not None:
            eq.status = EquipmentStatus.AVAILABLE
        r.status = ReservationStatus.COMPLETED
        return rec


class EquipmentService:
    """设备台账管理服务。"""

    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo

    def add(self, equipment: Equipment) -> Equipment:
        if self.repo.find_equipment(equipment.equip_id) is not None:
            raise ValidationError(f"设备编号已存在：{equipment.equip_id}")
        self.repo.add_equipment(equipment)
        return equipment

    def find_equipment(self, equip_id: str) -> Optional[Equipment]:
        """按编号查询设备，不存在返回 None。"""
        return self.repo.find_equipment(equip_id)

    def update(self, equip_id: str, **fields) -> Equipment:
        eq = self.repo.find_equipment(equip_id)
        if eq is None:
            raise NotFoundError(f"设备不存在：{equip_id}")
        for key, value in fields.items():
            if not hasattr(eq, key):
                raise ValidationError(f"设备无字段：{key}")
            setattr(eq, key, value)
        return eq

    def change_status(self, equip_id: str, status: EquipmentStatus) -> Equipment:
        eq = self.repo.find_equipment(equip_id)
        if eq is None:
            raise NotFoundError(f"设备不存在：{equip_id}")
        eq.status = status
        return eq

    def remove(self, equip_id: str) -> None:
        """逻辑删除：将设备置为「报废」。"""
        eq = self.repo.find_equipment(equip_id)
        if eq is None:
            raise NotFoundError(f"设备不存在：{equip_id}")
        eq.status = EquipmentStatus.SCRAPPED

    def query(self, category: Optional[str] = None,
              status: Optional[EquipmentStatus] = None,
              lab_id: Optional[str] = None) -> List[Equipment]:
        result = self.repo.list_equipments()
        if category:
            result = [e for e in result if e.category == category]
        if status:
            result = [e for e in result if e.status == status]
        if lab_id:
            result = [e for e in result if e.lab_id == lab_id]
        return result


class UserService:
    """用户注册与认证服务。"""

    def __init__(self, repo: InMemoryRepository) -> None:
        self.repo = repo

    def register(self, name: str, sid: str, role: Role, password: str,
                 phone: str = "", email: str = "") -> User:
        if self.repo.find_user_by_sid(sid) is not None:
            raise ValidationError(f"学号/工号已注册：{sid}")
        if not password or len(password) < 6:
            raise ValidationError("密码长度不能少于 6 位")
        user = User(
            user_id=f"U{sid}", name=name, sid=sid, role=role,
            password_hash=_hash_password(password), phone=phone, email=email,
        )
        self.repo.add_user(user)
        return user

    def login(self, sid: str, password: str) -> User:
        user = self.repo.find_user_by_sid(sid)
        if user is None:
            raise NotFoundError("账号不存在")
        if user.password_hash != _hash_password(password):
            raise PermissionError("密码错误")
        if user.status != "正常":
            raise PermissionError("账号已被禁用")
        return user
