# -*- coding: utf-8 -*-
"""主窗口基类：左侧导航 + 右侧堆叠页面 + 顶部用户信息与退出登录。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from utils.constants import ROLE_NAMES


class BaseMainWindow(QMainWindow):
    """带导航的主窗口基类，子类通过 add_page 挂载功能页。"""

    logged_out = pyqtSignal()

    def __init__(self, user: dict) -> None:
        super().__init__()
        self.user = user

        self.nav = QListWidget()
        self.nav.setFixedWidth(180)
        self.stack = QStackedWidget()

        header = QHBoxLayout()
        role_name = ROLE_NAMES.get(user["role"], "")
        self.info_label = QLabel(f"当前用户：{user['real_name']}（{role_name}）")
        logout_btn = QPushButton("退出登录")
        logout_btn.clicked.connect(self._logout)
        header.addWidget(self.info_label)
        header.addStretch(1)
        header.addWidget(logout_btn)

        body = QHBoxLayout()
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)

        central = QWidget()
        root = QVBoxLayout(central)
        root.addLayout(header)
        root.addLayout(body)
        self.setCentralWidget(central)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

    def add_page(self, name: str, widget: QWidget) -> None:
        """添加一个导航项及其页面。"""
        self.nav.addItem(name)
        self.stack.addWidget(widget)

    def _logout(self) -> None:
        self.logged_out.emit()
        self.close()
