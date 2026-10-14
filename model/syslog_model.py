# -*- coding: utf-8 -*-
"""系统日志表 DAO。"""

from db.base_model import BaseDAO


class SysLogDAO(BaseDAO):
    """系统日志数据访问对象。"""

    def insert(self, uid, op_content: str) -> int:
        return self.execute("INSERT INTO sys_log (uid, op_content) VALUES (?, ?)",
                            (uid, op_content))

    def list_all(self, limit: int = 200) -> list:
        return self.query_all(
            "SELECT s.*, u.real_name, u.username FROM sys_log s "
            "LEFT JOIN user u ON s.uid = u.uid ORDER BY s.log_id DESC LIMIT ?",
            (limit,))
