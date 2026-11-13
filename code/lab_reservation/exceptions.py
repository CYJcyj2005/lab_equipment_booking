# -*- coding: utf-8 -*-
"""自定义业务异常。

所有业务异常继承自 ReservationError，便于调用方统一捕获；
不同类型的异常对应不同的业务约束（见《软件需求规格说明书》3.3 / 3.4 节）。
"""


class ReservationError(Exception):
    """业务异常基类。"""


class ConflictError(ReservationError):
    """时段冲突：同一设备同一时段已存在有效预约。"""


class ValidationError(ReservationError):
    """输入校验失败：参数非法、设备不可预约等。"""


class NotFoundError(ReservationError):
    """目标对象不存在（设备 / 预约单 / 用户）。"""


class PermissionError(ReservationError):
    """权限不足：当前角色不允许执行该操作。"""


class StateError(ReservationError):
    """状态机非法迁移：当前状态下不允许执行该操作。"""
