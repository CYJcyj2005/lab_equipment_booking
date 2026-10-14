# -*- coding: utf-8 -*-
"""系统日志控制器。"""

from model.syslog_model import SysLogDAO


class LogController:
    """系统操作日志的写入与查询。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = SysLogDAO(db_path)

    def record(self, uid, op_content: str) -> None:
        """记录一条操作日志，uid 可为 None（系统操作）。"""
        self.dao.insert(uid, op_content)

    def list_all(self, limit: int = 200) -> list:
        return self.dao.list_all(limit)
