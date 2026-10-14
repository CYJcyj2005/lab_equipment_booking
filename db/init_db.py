# -*- coding: utf-8 -*-
"""建表 + 初始化超级管理员 + 种子数据。首次运行时调用，幂等。"""

import os
from contextlib import closing

from config import (BLACKLIST_THRESHOLD, DB_PATH, DEFAULT_ADMIN, MAX_BOOKING_HOURS,
                    MIN_CREDIT_SCORE, resolve_admin_password)
from db.base_model import BaseDAO
from utils.constants import ROLE_SUPER_ADMIN
from utils.crypto_util import hash_password

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    real_name TEXT NOT NULL,
    role INTEGER NOT NULL DEFAULT 1,
    status INTEGER NOT NULL DEFAULT 1,
    phone TEXT DEFAULT '',
    blacklist_count INTEGER NOT NULL DEFAULT 0,
    credit_score INTEGER NOT NULL DEFAULT 100,
    face_path TEXT DEFAULT '',
    create_time TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS lab (
    lid INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_name TEXT NOT NULL,
    location TEXT DEFAULT '',
    open_time TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    campus_id INTEGER
);

CREATE TABLE IF NOT EXISTS device (
    did INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_name TEXT NOT NULL,
    dev_no TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT '',
    lab_id INTEGER,
    spec TEXT DEFAULT '',
    status INTEGER NOT NULL DEFAULT 1,
    image_path TEXT DEFAULT '',
    remark TEXT DEFAULT '',
    total_count INTEGER NOT NULL DEFAULT 1,
    qr_code TEXT DEFAULT '',
    FOREIGN KEY (lab_id) REFERENCES lab(lid)
);

CREATE TABLE IF NOT EXISTS appointment (
    aid INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    did INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    apply_time TEXT DEFAULT (datetime('now', 'localtime')),
    audit_status INTEGER NOT NULL DEFAULT 0,
    audit_msg TEXT DEFAULT '',
    cancel_time TEXT DEFAULT '',
    appointment_type TEXT NOT NULL DEFAULT 'instant',
    tutor_uid INTEGER,
    approve_stage INTEGER NOT NULL DEFAULT 2,
    recurrence_group TEXT DEFAULT '',
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (did) REFERENCES device(did)
);

CREATE TABLE IF NOT EXISTS repair (
    rid INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    did INTEGER NOT NULL,
    content TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    deal_time TEXT DEFAULT '',
    deal_msg TEXT DEFAULT '',
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (did) REFERENCES device(did)
);

CREATE TABLE IF NOT EXISTS notice (
    nid INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    publisher_uid INTEGER NOT NULL,
    publish_time TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (publisher_uid) REFERENCES user(uid)
);

CREATE TABLE IF NOT EXISTS sys_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER,
    op_content TEXT NOT NULL,
    op_time TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS waitlist (
    wid INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    did INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    join_time TEXT DEFAULT (datetime('now', 'localtime')),
    status INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (did) REFERENCES device(did)
);

CREATE TABLE IF NOT EXISTS message (
    mid INTEGER PRIMARY KEY AUTOINCREMENT,
    receiver_uid INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    create_time TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (receiver_uid) REFERENCES user(uid)
);

CREATE TABLE IF NOT EXISTS setting (
    skey TEXT PRIMARY KEY,
    svalue TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campus (
    cid INTEGER PRIMARY KEY AUTOINCREMENT,
    campus_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS sign_in (
    sid INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    aid INTEGER,
    did INTEGER NOT NULL,
    sign_time TEXT DEFAULT (datetime('now', 'localtime')),
    method TEXT NOT NULL DEFAULT 'manual',
    result INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (aid) REFERENCES appointment(aid),
    FOREIGN KEY (did) REFERENCES device(did)
);

CREATE TABLE IF NOT EXISTS hardware_state (
    kind TEXT NOT NULL,
    ref_id INTEGER NOT NULL,
    state INTEGER NOT NULL DEFAULT 0,
    update_time TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (kind, ref_id)
);

CREATE TABLE IF NOT EXISTS device_metric (
    mid INTEGER PRIMARY KEY AUTOINCREMENT,
    did INTEGER NOT NULL,
    voltage REAL DEFAULT 0,
    current REAL DEFAULT 0,
    temperature REAL DEFAULT 0,
    online INTEGER NOT NULL DEFAULT 1,
    update_time TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (did) REFERENCES device(did)
);

CREATE TABLE IF NOT EXISTS credit_log (
    clid INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    change INTEGER NOT NULL,
    reason TEXT DEFAULT '',
    op_time TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (uid) REFERENCES user(uid)
);
"""


def init_db(db_path: str | None = None) -> None:
    """建表 + 迁移 + 初始化种子数据（幂等，可重复调用）。"""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with closing(BaseDAO(path)._connect()) as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        conn.commit()
    _seed(BaseDAO(path))


def _migrate(conn) -> None:
    """为已存在的旧库补充新增列（幂等）。"""
    _add_column(conn, "user", "credit_score", "INTEGER NOT NULL DEFAULT 100")
    _add_column(conn, "user", "face_path", "TEXT DEFAULT ''")
    _add_column(conn, "lab", "campus_id", "INTEGER")
    _add_column(conn, "device", "total_count", "INTEGER NOT NULL DEFAULT 1")
    _add_column(conn, "device", "qr_code", "TEXT DEFAULT ''")
    _add_column(conn, "appointment", "appointment_type", "TEXT NOT NULL DEFAULT 'instant'")
    _add_column(conn, "appointment", "tutor_uid", "INTEGER")
    _add_column(conn, "appointment", "approve_stage", "INTEGER NOT NULL DEFAULT 2")
    _add_column(conn, "appointment", "recurrence_group", "TEXT DEFAULT ''")


def _add_column(conn, table: str, column: str, ddl: str) -> None:
    """若表缺列则 ALTER TABLE 补列。"""
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _seed(dao: BaseDAO) -> None:
    """初始化超级管理员账号（若不存在）与演示校区/实验室/设备。"""
    if dao.query_one("SELECT uid FROM user WHERE username = ?",
                     (DEFAULT_ADMIN["username"],)) is None:
        pwd = resolve_admin_password()
        dao.execute(
            "INSERT INTO user (username, password_hash, real_name, role, phone) "
            "VALUES (?, ?, ?, ?, ?)",
            (DEFAULT_ADMIN["username"], hash_password(pwd),
             DEFAULT_ADMIN["real_name"], ROLE_SUPER_ADMIN, DEFAULT_ADMIN["phone"]),
        )

    if dao.query_one("SELECT cid FROM campus") is None:
        dao.execute("INSERT INTO campus (campus_name) VALUES ('本部校区')")
        dao.execute("INSERT INTO campus (campus_name) VALUES ('南校区')")

    if dao.query_one("SELECT lid FROM lab") is None:
        dao.execute("INSERT INTO lab (lab_name, location, open_time, campus_id) "
                    "VALUES (?, ?, ?, 1)", ("网络实验室", "N515", "08:00-22:00"))
        dao.execute("INSERT INTO lab (lab_name, location, open_time, campus_id) "
                    "VALUES (?, ?, ?, 1)", ("电子测量实验室", "N516", "08:00-22:00"))
        dao.execute("INSERT INTO lab (lab_name, location, open_time, campus_id) "
                    "VALUES (?, ?, ?, 2)", ("南校区电子实验室", "S201", "08:00-22:00"))

    if dao.query_one("SELECT did FROM device") is None:
        _devs = [
            ("示波器", "DEV-001", "电子测量", 1, "TBS1000", 5),
            ("函数信号发生器", "DEV-002", "电子测量", 1, "AFG1022", 4),
            ("逻辑分析仪", "DEV-003", "数字电路", 2, "LA1032", 3),
            ("数字万用表", "DEV-004", "电子测量", 2, "DM3058", 10),
            ("频谱分析仪", "DEV-005", "电子测量", 2, "RSA306B", 2),
            ("直流稳压电源", "DEV-006", "电源类", 1, "DP832", 6),
        ]
        for name, no, cat, lab, spec, total in _devs:
            dao.execute(
                "INSERT INTO device (dev_name, dev_no, category, lab_id, spec, status, total_count, qr_code) "
                "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
                (name, no, cat, lab, spec, total, f"DEV:{no}"))

    if dao.query_one("SELECT skey FROM setting WHERE skey = 'max_booking_hours'") is None:
        dao.execute("INSERT INTO setting (skey, svalue) VALUES ('max_booking_hours', ?)",
                    (str(MAX_BOOKING_HOURS),))
        dao.execute("INSERT INTO setting (skey, svalue) VALUES ('blacklist_threshold', ?)",
                    (str(BLACKLIST_THRESHOLD),))
        dao.execute("INSERT INTO setting (skey, svalue) VALUES ('min_credit_score', ?)",
                    (str(MIN_CREDIT_SCORE),))


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成：", DB_PATH)
