# -*- coding: utf-8 -*-
"""用户账号控制器：注册、登录、资料/密码、账号管理、黑名单。"""

from controller.log_controller import LogController
from model.user_model import UserDAO
from utils.constants import ROLE_STUDENT, USER_ACTIVE, USER_DISABLED
from utils.crypto_util import check_password, hash_password
from utils.validator import is_valid_password, is_valid_phone


class UserController:
    """用户账号业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = UserDAO(db_path)
        self.log = LogController(db_path)

    def register(self, username: str, password: str, real_name: str,
                 phone: str = "", role: int = ROLE_STUDENT) -> tuple:
        """注册账号（默认学生角色）。"""
        username = (username or "").strip()
        if not username:
            return False, "用户名不能为空"
        if not real_name.strip():
            return False, "真实姓名不能为空"
        if self.dao.get_by_username(username):
            return False, "用户名已被占用"
        if not is_valid_password(password):
            return False, "密码长度不能少于 6 位"
        if phone and not is_valid_phone(phone):
            return False, "手机号格式不正确"
        uid = self.dao.create(username, hash_password(password), real_name.strip(),
                              role, phone.strip())
        self.log.record(uid, f"用户注册：{username}")
        return True, "注册成功"

    def login(self, username: str, password: str) -> tuple:
        """登录校验，返回 (user_dict 或 None, 消息)。"""
        user = self.dao.get_by_username((username or "").strip())
        if not user:
            return None, "账号不存在"
        if not check_password(password, user["password_hash"]):
            return None, "密码错误"
        if user["status"] != USER_ACTIVE:
            return None, "账号已被禁用（黑名单），请联系管理员"
        self.log.record(user["uid"], f"登录成功：{user['username']}")
        return user, "登录成功"

    def update_profile(self, uid: int, **fields) -> tuple:
        self.dao.update_info(uid, **fields)
        return True, "个人信息已更新"

    def change_password(self, uid: int, old_password: str, new_password: str) -> tuple:
        user = self.dao.get_by_id(uid)
        if not check_password(old_password, user["password_hash"]):
            return False, "原密码错误"
        if not is_valid_password(new_password):
            return False, "新密码长度不能少于 6 位"
        self.dao.update_password(uid, hash_password(new_password))
        return True, "密码修改成功"

    # ---------- 账号管理（超级管理员） ----------
    def add_user(self, username: str, password: str, real_name: str,
                 role: int, phone: str = "") -> tuple:
        return self.register(username, password, real_name, phone, role)

    def reset_password(self, uid: int, new_password: str) -> tuple:
        if not is_valid_password(new_password):
            return False, "密码长度不能少于 6 位"
        self.dao.update_password(uid, hash_password(new_password))
        return True, "密码已重置"

    def set_status(self, uid: int, status: int) -> tuple:
        self.dao.set_status(uid, status)
        return True, "已禁用" if status == USER_DISABLED else "已启用"

    def list_users(self, keyword: str = "") -> list:
        return self.dao.list_all(keyword)
