# -*- coding: utf-8 -*-
"""集成测试：GUI 之下的 Controller → Model → SQLite 完整链路。"""

from datetime import timedelta

from test.common import BaseTestCase
from utils.constants import AUDIT_APPROVED, REPAIR_FIXED


class TestIntegration(BaseTestCase):
    def test_booking_full_chain(self):
        """学生提交预约 → 管理员审核通过 → 学生端可见已通过。"""
        start = self.future()
        ok, _ = self.appt_ctrl.submit_appointment(self.student1["uid"], self.dev1["did"],
                                                  start, start + timedelta(hours=2))
        self.assertTrue(ok)
        aid = self.appt_ctrl.list_by_user(self.student1["uid"])[0]["aid"]
        ok, _ = self.appt_ctrl.audit(aid, AUDIT_APPROVED, "", self.admin1)
        self.assertTrue(ok)
        my = self.appt_ctrl.list_by_user(self.student1["uid"])[0]
        self.assertEqual(my["audit_status"], AUDIT_APPROVED)
        # 审核结果推送到站内消息
        msgs = self.msg_ctrl.list_by_user(self.student1["uid"])
        self.assertTrue(any("审核" in m["title"] for m in msgs))

    def test_repair_chain(self):
        """学生报修 → 管理员处理 → 状态流转 + 消息通知。"""
        ok, _ = self.repair_ctrl.submit_repair(self.student1["uid"], self.dev1["did"],
                                               "屏幕无显示")
        self.assertTrue(ok)
        rid = self.repair_ctrl.list_by_user(self.student1["uid"])[0]["rid"]
        ok, _ = self.repair_ctrl.handle(rid, REPAIR_FIXED, "已更换屏幕", self.admin1["uid"])
        self.assertTrue(ok)
        self.assertEqual(self.repair_ctrl.list_by_user(self.student1["uid"])[0]["status"],
                         REPAIR_FIXED)

    def test_notice_chain(self):
        """管理员发公告 → 全员收到站内消息。"""
        ok, _ = self.notice_ctrl.publish("国庆放假安排", "实验室 10 月 1-7 日关闭",
                                         self.admin1["uid"])
        self.assertTrue(ok)
        self.assertTrue(any("新公告" in m["title"]
                            for m in self.msg_ctrl.list_by_user(self.student1["uid"])))
