# -*- coding: utf-8 -*-
"""DAO 基类：封装 SQLite 连接、游标、事务，供各 Model 继承。"""

import sqlite3
from contextlib import closing

from config import DB_PATH


class BaseDAO:
    """数据访问对象基类。

    子类直接调用 query_one / query_all / execute，无需关心连接与事务：
    - execute  执行写操作并提交，返回 lastrowid
    - query_one / query_all 返回 dict / list[dict]
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DB_PATH

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(self, sql: str, params: tuple = ()) -> int:
        """执行写操作并提交，返回 lastrowid。"""
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid

    def query_one(self, sql: str, params: tuple = ()) -> dict | None:
        """查询单行，无结果返回 None。"""
        with closing(self._connect()) as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def query_all(self, sql: str, params: tuple = ()) -> list:
        """查询多行，返回 dict 列表。"""
        with closing(self._connect()) as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
