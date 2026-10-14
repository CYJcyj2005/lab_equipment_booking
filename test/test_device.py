# -*- coding: utf-8 -*-
"""设备模块单元测试：增、查、状态。"""

from test.common import BaseTestCase
from utils.constants import DEVICE_REPAIR


class TestDevice(BaseTestCase):
    def test_add_device_success(self):
        ok, _ = self.device_ctrl.add_device("频谱仪", "DEV-999", "射频", 1, "N9000")
        self.assertTrue(ok)
        self.assertIsNotNone(self.device_ctrl.dao.get_by_no("DEV-999"))

    def test_add_device_duplicate_no(self):
        ok, msg = self.device_ctrl.add_device("重复", "DEV-001", "电子测量", 1)
        self.assertFalse(ok)

    def test_list_devices_keyword(self):
        result = self.device_ctrl.list_devices(keyword="示波")
        self.assertTrue(any(d["dev_no"] == "DEV-001" for d in result))

    def test_set_status(self):
        ok, _ = self.device_ctrl.set_status(self.dev1["did"], DEVICE_REPAIR)
        self.assertTrue(ok)
        self.assertEqual(self.device_ctrl.get_device(self.dev1["did"])["status"], DEVICE_REPAIR)
