# -*- coding: utf-8 -*-
"""用户注册与认证模块单元测试。"""

import os
import sys
import unittest

# 支持两种运行方式：`python -m unittest discover -s tests -t .` 与 IDE 直接运行本文件
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lab_reservation import Role
from lab_reservation.exceptions import NotFoundError, PermissionError, ValidationError

try:
    from .common import make_services
except ImportError:  # 直接运行本文件时无包上下文
    from common import make_services


class TestUserService(unittest.TestCase):
    def setUp(self):
        self.svc = make_services()

    def test_register_success(self):
        _, usvc, _, _, _, _ = self.svc
        u = usvc.register("李四", "2022002", Role.STUDENT, "xyz12345")
        self.assertEqual(u.sid, "2022002")

    def test_register_duplicate_sid(self):
        _, usvc, _, _, _, _ = self.svc
        with self.assertRaises(ValidationError):
            usvc.register("重复", "2022001", Role.STUDENT, "xyz12345")

    def test_register_short_password(self):
        _, usvc, _, _, _, _ = self.svc
        with self.assertRaises(ValidationError):
            usvc.register("李四", "2022002", Role.STUDENT, "123")

    def test_login_success(self):
        _, usvc, _, _, _, _ = self.svc
        u = usvc.login("2022001", "abc12345")
        self.assertEqual(u.name, "张三")

    def test_login_wrong_password(self):
        _, usvc, _, _, _, _ = self.svc
        with self.assertRaises(PermissionError):
            usvc.login("2022001", "wrong")

    def test_login_not_found(self):
        _, usvc, _, _, _, _ = self.svc
        with self.assertRaises(NotFoundError):
            usvc.login("9999999", "abc12345")


if __name__ == "__main__":
    unittest.main()
