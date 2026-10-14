# -*- coding: utf-8 -*-
"""SQLite 数据库备份 / 恢复（路径可注入，便于单元测试）。"""

import os
import shutil
from datetime import datetime

from config import BACKUP_DIR, DB_PATH


def backup_database(db_path: str | None = None,
                    backup_dir: str | None = None) -> tuple:
    """备份数据库文件，返回 (是否成功, 消息/目标路径)。"""
    db_path = db_path or DB_PATH
    backup_dir = backup_dir or BACKUP_DIR
    if not os.path.exists(db_path):
        return False, "数据库文件不存在"
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(backup_dir, f"device_booking_{stamp}.db")
    try:
        shutil.copy2(db_path, target)
        return True, target
    except Exception as e:  # pragma: no cover - 环境异常
        return False, str(e)


def list_backups(backup_dir: str | None = None) -> list:
    """列出所有备份文件名（按时间倒序）。"""
    backup_dir = backup_dir or BACKUP_DIR
    if not os.path.isdir(backup_dir):
        return []
    return sorted(
        (f for f in os.listdir(backup_dir) if f.endswith(".db")),
        reverse=True,
    )


def restore_database(filename: str, db_path: str | None = None,
                     backup_dir: str | None = None) -> tuple:
    """从备份文件恢复数据库，返回 (是否成功, 消息)。"""
    db_path = db_path or DB_PATH
    backup_dir = backup_dir or BACKUP_DIR
    src = os.path.join(backup_dir, filename)
    if not os.path.exists(src):
        return False, "备份文件不存在"
    try:
        shutil.copy2(src, db_path)
        return True, "恢复成功"
    except Exception as e:  # pragma: no cover - 环境异常
        return False, str(e)
