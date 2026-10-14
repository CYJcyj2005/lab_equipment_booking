# -*- coding: utf-8 -*-
"""全局状态常量（与数据库整型取值保持一致）。"""

# 角色
ROLE_STUDENT = 1
ROLE_LAB_ADMIN = 2
ROLE_SUPER_ADMIN = 3
ROLE_TEACHER = 4

ROLE_NAMES = {
    ROLE_STUDENT: "学生",
    ROLE_LAB_ADMIN: "实验室管理员",
    ROLE_SUPER_ADMIN: "超级管理员",
    ROLE_TEACHER: "教师/导师",
}

# 账号状态
USER_ACTIVE = 1
USER_DISABLED = 0

# 设备状态
DEVICE_IDLE = 1
DEVICE_IN_USE = 2
DEVICE_REPAIR = 3
DEVICE_SCRAPPED = 4

DEVICE_STATUS_NAMES = {
    DEVICE_IDLE: "空闲",
    DEVICE_IN_USE: "占用",
    DEVICE_REPAIR: "维修",
    DEVICE_SCRAPPED: "报废",
}

# 预约审核状态
AUDIT_PENDING = 0
AUDIT_APPROVED = 1
AUDIT_REJECTED = 2
AUDIT_CANCELLED = 3
AUDIT_COMPLETED = 4
AUDIT_NO_SHOW = 5

AUDIT_STATUS_NAMES = {
    AUDIT_PENDING: "待审核",
    AUDIT_APPROVED: "已通过",
    AUDIT_REJECTED: "已驳回",
    AUDIT_CANCELLED: "已取消",
    AUDIT_COMPLETED: "已完成",
    AUDIT_NO_SHOW: "爽约",
}

# 报修状态
REPAIR_PENDING = 0
REPAIR_IN_PROGRESS = 1
REPAIR_FIXED = 2

REPAIR_STATUS_NAMES = {
    REPAIR_PENDING: "待处理",
    REPAIR_IN_PROGRESS: "维修中",
    REPAIR_FIXED: "已修复",
}

# 候补状态
WAIT_WAITING = 0
WAIT_PROMOTED = 1
WAIT_CANCELLED = 2
WAIT_EXPIRED = 3

WAIT_STATUS_NAMES = {
    WAIT_WAITING: "等待中",
    WAIT_PROMOTED: "已转正",
    WAIT_CANCELLED: "已取消",
    WAIT_EXPIRED: "已失效",
}

# 签到方式
SIGN_FACE = "face"
SIGN_MANUAL = "manual"

SIGN_METHOD_NAMES = {
    SIGN_FACE: "人脸识别",
    SIGN_MANUAL: "手动签到",
}

# 硬件联动类型
HW_DOOR = "door"      # 门禁
HW_POWER = "power"    # 电源

HW_KIND_NAMES = {
    HW_DOOR: "门禁",
    HW_POWER: "电源",
}

# 预约类型
APPT_INSTANT = "instant"      # 即时预约（先到先得，管理员审核）
APPT_APPROVAL = "approval"    # 审批预约（导师 → 管理员多级审批）
APPT_WEEKLY = "weekly"        # 周期性预约（每周固定时段）

APPT_TYPE_NAMES = {
    APPT_INSTANT: "即时预约",
    APPT_APPROVAL: "审批预约",
    APPT_WEEKLY: "周期性预约",
}

# 多级审批阶段
STAGE_TUTOR = 1    # 待导师审核
STAGE_ADMIN = 2    # 待管理员审核

# 信用分
CREDIT_INIT = 100          # 初始信用分
CREDIT_NO_SHOW_PENALTY = 20  # 爽约扣分
