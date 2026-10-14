# -*- coding: utf-8 -*-
"""超级管理员主窗口：账号管理、黑名单、系统参数、日志、数据备份恢复。"""

from PyQt6.QtWidgets import (
    QFormLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QPushButton, QVBoxLayout, QWidget,
)

from controller.appointment_controller import AppointmentController
from controller.log_controller import LogController
from controller.setting_controller import SettingController
from controller.user_controller import UserController
from model.campus_model import CampusDAO
from utils.backup_util import backup_database, list_backups, restore_database
from utils.constants import ROLE_NAMES, USER_ACTIVE, USER_DISABLED
from view.base_window import BaseMainWindow
from view.chart_widget import build_stats_chart
from view.widgets import UserDialog, confirm, fill_table, info, make_table, warn


class SuperAdminWindow(BaseMainWindow):
    """超级管理员端主窗口。"""

    def __init__(self, user: dict) -> None:
        super().__init__(user)
        self.setWindowTitle("实验室设备预约系统 - 超级管理员端")
        self.resize(1100, 700)

        self.user_ctrl = UserController()
        self.setting_ctrl = SettingController()
        self.log_ctrl = LogController()
        self.appt_ctrl = AppointmentController()
        self.campus_dao = CampusDAO()

        self.add_page("账号管理", self._page_accounts())
        self.add_page("黑名单", self._page_blacklist())
        self.add_page("校区管理", self._page_campuses())
        self.add_page("系统参数", self._page_settings())
        self.add_page("系统日志", self._page_logs())
        self.add_page("统计图表", self._page_charts())
        self.add_page("数据备份恢复", self._page_backup())

    # ---------- 账号管理 ----------
    def _page_accounts(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.user_table = make_table(["ID", "用户名", "姓名", "角色", "状态", "手机", "爽约次数"])
        v.addWidget(self.user_table)
        btns = QHBoxLayout()
        add_btn = QPushButton("新增账号")
        add_btn.clicked.connect(self._add_account)
        reset_btn = QPushButton("重置密码")
        reset_btn.clicked.connect(self._reset_password)
        toggle_btn = QPushButton("禁用/启用")
        toggle_btn.clicked.connect(self._toggle_status)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_accounts)
        for b in (add_btn, reset_btn, toggle_btn, refresh_btn):
            btns.addWidget(b)
        btns.addStretch(1)
        v.addLayout(btns)
        self._refresh_accounts()
        return w

    def _user_rows(self, rows: list) -> list:
        for r in rows:
            r["role_name"] = ROLE_NAMES.get(r["role"], "")
            r["status_name"] = "正常" if r["status"] == USER_ACTIVE else "禁用"
        return rows

    def _refresh_accounts(self) -> None:
        fill_table(self.user_table, self._user_rows(self.user_ctrl.list_users()),
                   ["uid", "username", "real_name", "role_name", "status_name",
                    "phone", "blacklist_count"])

    def _selected_uid(self) -> int | None:
        row = self.user_table.currentRow()
        if row < 0:
            warn("请先选择一名用户")
            return None
        return int(self.user_table.item(row, 0).text())

    def _add_account(self) -> None:
        dlg = UserDialog(self)
        if dlg.exec() != UserDialog.DialogCode.Accepted:
            return
        f = dlg.values()
        ok, msg = self.user_ctrl.add_user(f["username"], f["password"],
                                          f["real_name"], f["role"], f["phone"])
        info(msg) if ok else warn(msg)
        self._refresh_accounts()

    def _reset_password(self) -> None:
        uid = self._selected_uid()
        if not uid:
            return
        pwd, ok = QInputDialog.getText(self, "重置密码", "输入新密码：",
                                       QLineEdit.EchoMode.Password)
        if not ok:
            return
        ok, msg = self.user_ctrl.reset_password(uid, pwd)
        info(msg) if ok else warn(msg)

    def _toggle_status(self) -> None:
        uid = self._selected_uid()
        if not uid:
            return
        user = self.user_ctrl.dao.get_by_id(uid)
        new_status = USER_DISABLED if user["status"] == USER_ACTIVE else USER_ACTIVE
        ok, msg = self.user_ctrl.set_status(uid, new_status)
        info(msg) if ok else warn(msg)
        self._refresh_accounts()

    # ---------- 黑名单 ----------
    def _page_blacklist(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        hint = QLabel("黑名单（账号被禁用的用户）。可通过下方按钮移出黑名单并清零爽约次数。")
        hint.setStyleSheet("color:gray;")
        v.addWidget(hint)
        self.bl_table = make_table(["ID", "用户名", "姓名", "爽约次数", "状态"])
        v.addWidget(self.bl_table)
        btns = QHBoxLayout()
        remove_btn = QPushButton("移出黑名单（启用并清零）")
        remove_btn.clicked.connect(self._remove_blacklist)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_blacklist)
        btns.addWidget(remove_btn)
        btns.addWidget(refresh_btn)
        btns.addStretch(1)
        v.addLayout(btns)
        self._refresh_blacklist()
        return w

    def _refresh_blacklist(self) -> None:
        rows = [u for u in self.user_ctrl.list_users() if u["status"] == USER_DISABLED]
        fill_table(self.bl_table, rows,
                   ["uid", "username", "real_name", "blacklist_count", "status"])

    def _remove_blacklist(self) -> None:
        row = self.bl_table.currentRow()
        if row < 0:
            warn("请先选择一名黑名单用户")
            return
        uid = int(self.bl_table.item(row, 0).text())
        if not confirm("确认将该用户移出黑名单并清零爽约次数？"):
            return
        self.user_ctrl.set_status(uid, USER_ACTIVE)
        self.user_ctrl.dao.set_blacklist_count(uid, 0)
        info("已移出黑名单")
        self._refresh_blacklist()

    # ---------- 校区管理 ----------
    def _page_campuses(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("校区列表（多校区分级管理）："))
        self.campus_list = QListWidget()
        v.addWidget(self.campus_list)
        btns = QHBoxLayout()
        add_btn = QPushButton("新增校区")
        add_btn.clicked.connect(self._add_campus)
        del_btn = QPushButton("删除选中校区")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._del_campus)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_campuses)
        btns.addWidget(add_btn)
        btns.addWidget(del_btn)
        btns.addWidget(refresh_btn)
        btns.addStretch(1)
        v.addLayout(btns)
        self._refresh_campuses()
        return w

    def _refresh_campuses(self) -> None:
        self.campus_list.clear()
        self.campus_list.addItems([c["campus_name"] for c in self.campus_dao.list_all()])

    def _add_campus(self) -> None:
        name, ok = QInputDialog.getText(self, "新增校区", "校区名称：")
        if not ok or not name.strip():
            return
        if self.campus_dao.get_by_name(name.strip()):
            warn("校区已存在")
            return
        self.campus_dao.create(name.strip())
        self._refresh_campuses()

    def _del_campus(self) -> None:
        item = self.campus_list.currentItem()
        if not item:
            warn("请先选择一个校区")
            return
        campus = self.campus_dao.get_by_name(item.text())
        if not campus:
            return
        if not confirm(f"确认删除校区「{item.text()}」？该校区下的实验室将失去归属。"):
            return
        self.campus_dao.delete(campus["cid"])
        self._refresh_campuses()

    # ---------- 统计图表 ----------
    def _page_charts(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        refresh_btn = QPushButton("刷新图表")
        refresh_btn.clicked.connect(self._refresh_charts)
        v.addWidget(refresh_btn)
        self.chart_container = QVBoxLayout()
        v.addLayout(self.chart_container)
        self._refresh_charts()
        return w

    def _refresh_charts(self) -> None:
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.chart_container.addWidget(build_stats_chart(self.appt_ctrl.list_all()))

    # ---------- 系统参数 ----------
    def _page_settings(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        form = QFormLayout()
        self.max_hours_edit = QLineEdit(str(self.setting_ctrl.get_int("max_booking_hours", 4)))
        self.threshold_edit = QLineEdit(str(self.setting_ctrl.get_int("blacklist_threshold", 3)))
        form.addRow("单次预约最大时长（小时）：", self.max_hours_edit)
        form.addRow("爽约次数黑名单阈值：", self.threshold_edit)
        v.addLayout(form)
        save_btn = QPushButton("保存参数")
        save_btn.clicked.connect(self._save_settings)
        v.addWidget(save_btn)
        v.addWidget(QLabel("参数保存后立即生效，作用于后续预约校验与爽约判定。"))
        v.addStretch(1)
        return w

    def _save_settings(self) -> None:
        try:
            max_hours = int(self.max_hours_edit.text())
            threshold = int(self.threshold_edit.text())
            if max_hours <= 0 or threshold <= 0:
                raise ValueError
        except ValueError:
            warn("请输入正整数")
            return
        self.setting_ctrl.set("max_booking_hours", max_hours)
        self.setting_ctrl.set("blacklist_threshold", threshold)
        info("参数已保存")

    # ---------- 系统日志 ----------
    def _page_logs(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        self.log_table = make_table(["ID", "操作人", "操作内容", "时间"])
        v.addWidget(self.log_table)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_logs)
        v.addWidget(refresh_btn)
        self._refresh_logs()
        return w

    def _refresh_logs(self) -> None:
        fill_table(self.log_table, self.log_ctrl.list_all(),
                   ["log_id", "real_name", "op_content", "op_time"])

    # ---------- 数据备份恢复 ----------
    def _page_backup(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        btns = QHBoxLayout()
        backup_btn = QPushButton("立即备份数据库")
        backup_btn.clicked.connect(self._backup)
        btns.addWidget(backup_btn)
        btns.addStretch(1)
        v.addLayout(btns)

        v.addWidget(QLabel("已有备份："))
        self.backup_list = QListWidget()
        v.addWidget(self.backup_list)

        restore_btn = QPushButton("恢复选中备份")
        restore_btn.clicked.connect(self._restore)
        v.addWidget(restore_btn)
        self._refresh_backups()
        return w

    def _refresh_backups(self) -> None:
        self.backup_list.clear()
        self.backup_list.addItems(list_backups())

    def _backup(self) -> None:
        ok, msg = backup_database()
        info(f"备份成功：{msg}") if ok else warn(msg)
        self._refresh_backups()

    def _restore(self) -> None:
        item = self.backup_list.currentItem()
        if not item:
            warn("请先选择一个备份文件")
            return
        if not confirm("恢复将覆盖当前数据库，确认继续？"):
            return
        ok, msg = restore_database(item.text())
        info(msg) if ok else warn(msg)
