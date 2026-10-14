# -*- coding: utf-8 -*-
"""实验室设备预约系统 —— 程序入口。

运行方式：
    python main.py

首次运行会自动创建 SQLite 数据库、初始化超级管理员（密码随机生成并写入
db/admin_secret.txt，仅开发人员可见，UI 不展示明文）并写入种子数据。
"""

import os
import sys

from PyQt6.QtWidgets import QApplication

from config import BASE_DIR
from db.init_db import init_db
from view.login_window import LoginWindow


def _load_style(app: QApplication) -> None:
    """加载微信风格 QSS（缺失时静默跳过）。"""
    qss_path = os.path.join(BASE_DIR, "view", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("LabEquipmentBooking")
    app.setOrganizationName("LabBooking")
    _load_style(app)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
