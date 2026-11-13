# -*- coding: utf-8 -*-
"""实验室设备预约系统 —— 核心业务模块包。

本包实现课程设计「实验室设备预约系统」的核心模块（设备管理、预约管理、审核管理），
用于软件工程实验 6（编码规范与模块化编程）与实验 9（单元测试）。

模块划分：
    models        —— 数据模型（用户、实验室、设备、预约单、使用记录）
    exceptions    —— 自定义业务异常
    repositories  —— 内存数据仓库（演示用，可替换为数据库实现）
    services      —— 业务逻辑层（预约、审核、设备、用户服务）
"""

from .models import (
    Role, EquipmentStatus, ReservationStatus,
    User, Lab, Equipment, Reservation, UsageRecord,
)
from .exceptions import (
    ReservationError, ConflictError, ValidationError,
    NotFoundError, PermissionError, StateError,
)
from .services import ReservationService, EquipmentService, UserService

__all__ = [
    "Role", "EquipmentStatus", "ReservationStatus",
    "User", "Lab", "Equipment", "Reservation", "UsageRecord",
    "ReservationError", "ConflictError", "ValidationError",
    "NotFoundError", "PermissionError", "StateError",
    "ReservationService", "EquipmentService", "UserService",
]
