# -*- coding: utf-8 -*-
"""用户表 DAO。"""

from db.base_model import BaseDAO


class UserDAO(BaseDAO):
    """用户数据访问对象。"""

    def create(self, username: str, password_hash: str, real_name: str,
               role: int, phone: str = "") -> int:
        """新增用户，返回 uid。"""
        return self.execute(
            "INSERT INTO user (username, password_hash, real_name, role, phone) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, real_name, role, phone),
        )

    def get_by_id(self, uid: int) -> dict | None:
        return self.query_one("SELECT * FROM user WHERE uid = ?", (uid,))

    def get_by_username(self, username: str) -> dict | None:
        return self.query_one("SELECT * FROM user WHERE username = ?", (username,))

    def update_info(self, uid: int, **fields) -> None:
        """更新允许修改的个人信息字段（real_name / phone）。"""
        allowed = {"real_name", "phone"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        self.execute(f"UPDATE user SET {set_clause} WHERE uid = ?",
                     (*updates.values(), uid))

    def update_password(self, uid: int, password_hash: str) -> None:
        self.execute("UPDATE user SET password_hash = ? WHERE uid = ?",
                     (password_hash, uid))

    def set_status(self, uid: int, status: int) -> None:
        self.execute("UPDATE user SET status = ? WHERE uid = ?", (status, uid))

    def set_blacklist_count(self, uid: int, count: int) -> None:
        self.execute("UPDATE user SET blacklist_count = ? WHERE uid = ?", (count, uid))

    def set_credit_score(self, uid: int, score: int) -> None:
        self.execute("UPDATE user SET credit_score = ? WHERE uid = ?", (score, uid))

    def set_face_path(self, uid: int, face_path: str) -> None:
        self.execute("UPDATE user SET face_path = ? WHERE uid = ?", (face_path, uid))

    def list_by_role(self, role: int) -> list:
        return self.query_all("SELECT * FROM user WHERE role = ? ORDER BY uid", (role,))

    def list_all(self, keyword: str = "") -> list:
        """列出全部用户，支持按用户名/姓名模糊搜索。"""
        if keyword:
            like = f"%{keyword}%"
            return self.query_all(
                "SELECT * FROM user WHERE username LIKE ? OR real_name LIKE ? "
                "ORDER BY uid", (like, like))
        return self.query_all("SELECT * FROM user ORDER BY uid")
