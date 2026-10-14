# -*- coding: utf-8 -*-
"""用户模块单元测试：注册、登录、改密。"""

from test.common import BaseTestCase


class TestUserRegister(BaseTestCase):
    def test_register_success(self):
        ok, msg = self.user_ctrl.register("newbie", "abc12345", "王五", "13900000000")
        self.assertTrue(ok, msg)
        self.assertIsNotNone(self.user_ctrl.dao.get_by_username("newbie"))

    def test_register_duplicate_username(self):
        ok, msg = self.user_ctrl.register("student1", "abc12345", "重复")
        self.assertFalse(ok)
        self.assertIn("已被占用", msg)

    def test_register_short_password(self):
        ok, msg = self.user_ctrl.register("x", "123", "短密码")
        self.assertFalse(ok)

    def test_register_invalid_phone(self):
        ok, msg = self.user_ctrl.register("y", "abc12345", "手机号", "123")
        self.assertFalse(ok)


class TestUserLogin(BaseTestCase):
    def test_login_success(self):
        user, msg = self.user_ctrl.login("student1", "abc12345")
        self.assertIsNotNone(user)
        self.assertEqual(user["real_name"], "张三")

    def test_login_wrong_password(self):
        user, msg = self.user_ctrl.login("student1", "wrong")
        self.assertIsNone(user)

    def test_login_not_found(self):
        user, msg = self.user_ctrl.login("nobody", "abc12345")
        self.assertIsNone(user)

    def test_change_password(self):
        ok, _ = self.user_ctrl.change_password(self.student1["uid"], "abc12345", "newpass123")
        self.assertTrue(ok)
        user, _ = self.user_ctrl.login("student1", "newpass123")
        self.assertIsNotNone(user)
