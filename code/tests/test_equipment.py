# -*- coding: utf-8 -*-
"""设备台账管理模块单元测试。"""

import os
import sys
import unittest

# 支持两种运行方式：`python -m unittest discover -s tests -t .` 与 IDE 直接运行本文件
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lab_reservation import Equipment, EquipmentStatus
from lab_reservation.exceptions import NotFoundError, ValidationError

try:
    from .common import make_services
except ImportError:  # 直接运行本文件时无包上下文
    from common import make_services


class TestEquipmentService(unittest.TestCase):
    def setUp(self):
        self.svc = make_services()

    def test_add_success(self):
        _, _, esvc, _, _, _ = self.svc
        eq = esvc.add(Equipment("E10", "频谱仪", "电子测量", "L01"))
        self.assertEqual(eq.equip_id, "E10")

    def test_add_duplicate(self):
        _, _, esvc, _, _, _ = self.svc
        with self.assertRaises(ValidationError):
            esvc.add(Equipment("E01", "重复设备", "电子测量", "L01"))

    def test_update(self):
        _, _, esvc, _, _, _ = self.svc
        esvc.update("E01", name="数字示波器")
        self.assertEqual(esvc.find_equipment("E01").name, "数字示波器")

    def test_update_not_found(self):
        _, _, esvc, _, _, _ = self.svc
        with self.assertRaises(NotFoundError):
            esvc.update("E99", name="x")

    def test_change_status(self):
        _, _, esvc, _, _, _ = self.svc
        esvc.change_status("E01", EquipmentStatus.SCRAPPED)
        self.assertEqual(esvc.find_equipment("E01").status, EquipmentStatus.SCRAPPED)

    def test_remove_sets_scrapped(self):
        _, _, esvc, _, _, _ = self.svc
        esvc.remove("E01")
        self.assertEqual(esvc.find_equipment("E01").status, EquipmentStatus.SCRAPPED)

    def test_query_by_category(self):
        _, _, esvc, _, _, _ = self.svc
        result = esvc.query(category="电子测量")
        self.assertEqual(len(result), 2)

    def test_query_by_status(self):
        _, _, esvc, _, _, _ = self.svc
        esvc.change_status("E01", EquipmentStatus.REPAIR)
        result = esvc.query(status=EquipmentStatus.REPAIR)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].equip_id, "E01")


if __name__ == "__main__":
    unittest.main()
