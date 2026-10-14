# -*- coding: utf-8 -*-
"""密码加密工具（bcrypt，禁止明文存储）。"""

import bcrypt


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希，返回字符串形式。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
