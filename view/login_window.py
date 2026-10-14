# -*- coding: utf-8 -*-
"""登录窗口：全角色登录入口，按角色跳转对应主窗口。

支持「记住账号 / 记住密码」：账号默认记忆；密码明文存于 QSettings，
仅在用户主动勾选「记住密码」时保存，并弹窗提示安全风险。
"""

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from controller.user_controller import UserController
from utils.constants import ROLE_LAB_ADMIN, ROLE_SUPER_ADMIN, ROLE_TEACHER
from view.lab_admin_window import LabAdminWindow
from view.register_window import RegisterWindow
from view.student_main_window import StudentMainWindow
from view.super_admin_window import SuperAdminWindow
from view.teacher_window import TeacherWindow


class LoginWindow(QWidget):
    """登录窗口。登录成功后关闭自身并打开对应角色主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("实验室设备预约系统 - 登录")
        self.setFixedSize(400, 360)
        self.user_ctrl = UserController()
        self._main_win = None
        self._reg_win = None
        self.settings = QSettings("LabBooking", "LabEquipmentBooking")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel("实验室设备预约系统")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Lab Equipment Booking")
        sub.setStyleSheet("color:#999999;font-size:12px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(12)

        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("请输入用户名")
        self.password = QLineEdit()
        self.password.setPlaceholderText("请输入密码")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("用户名：", self.username)
        form.addRow("密码：", self.password)
        layout.addLayout(form)

        opts = QHBoxLayout()
        self.remember_user = QCheckBox("记住账号")
        self.remember_user.setChecked(True)
        self.remember_pwd = QCheckBox("记住密码")
        self.remember_pwd.toggled.connect(self._on_remember_pwd)
        opts.addWidget(self.remember_user)
        opts.addWidget(self.remember_pwd)
        opts.addStretch(1)
        layout.addLayout(opts)

        login_btn = QPushButton("登录")
        login_btn.setMinimumHeight(38)
        login_btn.clicked.connect(self._login)
        layout.addWidget(login_btn)

        reg_btn = QPushButton("注册学生账号")
        reg_btn.setObjectName("ghost")
        reg_btn.clicked.connect(self._register)
        layout.addWidget(reg_btn)
        layout.addStretch(1)

        self._restore_saved()

    # ---------- 记住账号 / 密码 ----------
    def _restore_saved(self) -> None:
        last_user = self.settings.value("last_username", "", type=str)
        if last_user:
            self.username.setText(last_user)
        self.remember_pwd.setChecked(self.settings.value("remember_pwd", False, type=bool))
        if self.remember_pwd.isChecked():
            self.password.setText(self.settings.value("saved_password", "", type=str))

    def _save_login(self) -> None:
        if self.remember_user.isChecked():
            self.settings.setValue("last_username", self.username.text().strip())
        else:
            self.settings.setValue("last_username", "")
        self.settings.setValue("remember_pwd", self.remember_pwd.isChecked())
        if self.remember_pwd.isChecked():
            self.settings.setValue("saved_password", self.password.text())
        else:
            self.settings.setValue("saved_password", "")

    def _on_remember_pwd(self, checked: bool) -> None:
        if checked:
            QMessageBox.information(
                self, "安全提示",
                "「记住密码」将以明文形式保存在本机配置中，存在泄露风险。\n"
                "建议仅在个人电脑上使用。")

    # ---------- 登录 / 注册 ----------
    def _login(self) -> None:
        user, msg = self.user_ctrl.login(self.username.text(), self.password.text())
        if not user:
            QMessageBox.warning(self, "登录失败", msg)
            return
        self._save_login()
        self._open_main(user)

    def _register(self) -> None:
        self._reg_win = RegisterWindow()
        self._reg_win.show()

    def _open_main(self, user: dict) -> None:
        if user["role"] == ROLE_LAB_ADMIN:
            win = LabAdminWindow(user)
        elif user["role"] == ROLE_SUPER_ADMIN:
            win = SuperAdminWindow(user)
        elif user["role"] == ROLE_TEACHER:
            win = TeacherWindow(user)
        else:
            win = StudentMainWindow(user)
        self._main_win = win
        win.logged_out.connect(self._on_logout)
        self.close()
        win.show()

    def _on_logout(self) -> None:
        self.password.clear()
        self.show()
