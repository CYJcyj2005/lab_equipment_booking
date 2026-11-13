# -*- coding: utf-8 -*-
"""接口测试配套服务：用临时数据库启动 Flask API（127.0.0.1:5001）。

集合 docs/api_test.postman_collection.json 依赖本脚本预置的两个学生账号
（stuA / stuB）与一张已通过的预约单，用于验证“多台设备并发占用”和“签到”。

用法（在仓库根目录）：
    python docs/api_test_server.py
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from controller.user_controller import UserController  # noqa: E402
from db.base_model import BaseDAO  # noqa: E402
from server.app import create_app  # noqa: E402
from utils.time_util import to_db_str  # noqa: E402

DB = os.path.join(tempfile.gettempdir(), "lab_booking_api_test.db")


def main() -> None:
    if os.path.exists(DB):
        os.remove(DB)

    app = create_app(DB)
    uc = UserController(DB)
    for username, name, phone in (
        ("stuA", "测试学生A", "13800000001"),
        ("stuB", "测试学生B", "13800000002"),
    ):
        okk, msg = uc.register(username, "abc12345", name, phone)
        print(username, okk, msg)

    # stuA 的“已通过”预约单：时段覆盖当前时间，供签到接口测试
    uid_a = uc.dao.get_by_username("stuA")["uid"]
    now = datetime.now()
    BaseDAO(DB).execute(
        "INSERT INTO appointment (uid, did, start_time, end_time, audit_status, approve_stage) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (uid_a, 6, to_db_str(now - timedelta(minutes=10)),
         to_db_str(now + timedelta(minutes=50)), 1, 0),
    )
    print("ready:", DB)
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
