# -*- coding: utf-8 -*-
"""统一输入校验。"""

import re

PHONE_RE = re.compile(r"^1\d{10}$")


def is_valid_phone(phone: str) -> bool:
    """校验 11 位大陆手机号。"""
    return bool(PHONE_RE.match(phone or ""))


def is_valid_password(password: str) -> bool:
    """校验密码长度不少于 6 位。"""
    return bool(password) and len(password) >= 6
