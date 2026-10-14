# -*- coding: utf-8 -*-
"""全局配置：数据库路径、业务参数、默认账号。"""

import os
import secrets
import string

# 项目根目录（config.py 所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "device_booking.db")
BACKUP_DIR = os.path.join(DB_DIR, "backup")

# 超级管理员初始密码密文文件（仅开发人员可见，加入 .gitignore）
ADMIN_SECRET_FILE = os.path.join(DB_DIR, "admin_secret.txt")

# 预约业务参数
MAX_BOOKING_HOURS = 4          # 单次预约最大时长（小时）
BLACKLIST_THRESHOLD = 3        # 爽约累计达到该值即禁用账号（加入黑名单）
CANCEL_DEADLINE_MINUTES = 30   # 距开始不足该分钟数不可取消
MIN_CREDIT_SCORE = 60          # 信用分低于该值禁止预约

# 初始超级管理员账号（首次初始化时创建；密码见 resolve_admin_password）
DEFAULT_ADMIN = {
    "username": "admin",
    "real_name": "超级管理员",
    "phone": "13800000000",
}


def _generate_password(length: int = 16) -> str:
    """生成随机强密码（字母 + 数字 + 特殊字符）。"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def resolve_admin_password() -> str:
    """解析超级管理员初始密码。

    优先级：环境变量 SUPER_ADMIN_PWD > db/admin_secret.txt > 随机生成并写入密文文件。
    仅在首次创建超管账号时调用，避免在 UI / 日志中暴露明文。
    """
    env = os.environ.get("SUPER_ADMIN_PWD")
    if env:
        return env
    if os.path.exists(ADMIN_SECRET_FILE):
        with open(ADMIN_SECRET_FILE, "r", encoding="utf-8") as f:
            pwd = f.read().strip()
        if pwd:
            return pwd
    pwd = _generate_password()
    os.makedirs(DB_DIR, exist_ok=True)
    with open(ADMIN_SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(pwd)
    return pwd
