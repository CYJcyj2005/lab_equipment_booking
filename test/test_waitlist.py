# -*- coding: utf-8 -*-
"""候补队列模块单元测试（UT-08 / UT-09）。"""

from datetime import timedelta

from test.common import BaseTestCase
from utils.constants import WAIT_CANCELLED, WAIT_PROMOTED


class TestWaitlist(BaseTestCase):
    def test_join_and_cancel(self):
        start = self.future()
        ok, _ = self.waitlist_ctrl.join(self.student1["uid"], self.dev1["did"],
                                        start, start + timedelta(hours=2))
        self.assertTrue(ok)
        wid = self.waitlist_ctrl.list_by_user(self.student1["uid"])[0]["wid"]
        ok, _ = self.waitlist_ctrl.cancel(wid, self.student1["uid"])
        self.assertTrue(ok)
        self.assertEqual(self.waitlist_ctrl.dao.get_by_id(wid)["status"], WAIT_CANCELLED)

    def test_cancel_others_waitlist_denied(self):
        start = self.future()
        self.waitlist_ctrl.join(self.student1["uid"], self.dev1["did"],
                                start, start + timedelta(hours=2))
        wid = self.waitlist_ctrl.list_by_user(self.student1["uid"])[0]["wid"]
        ok, _ = self.waitlist_ctrl.cancel(wid, self.student2["uid"])
        self.assertFalse(ok)

    def test_cancel_appointment_promotes_waitlist(self):  # UT-08 / UT-09
        start = self.future()
        # 学生2 先预约占住时段
        self.appt_ctrl.submit_appointment(self.student2["uid"], self.dev1["did"],
                                          start, start + timedelta(hours=2))
        # 学生1 加入候补
        self.waitlist_ctrl.join(self.student1["uid"], self.dev1["did"],
                                start, start + timedelta(hours=2))
        # 学生2 取消预约
        aid = self.appt_ctrl.list_by_user(self.student2["uid"])[0]["aid"]
        ok, _ = self.appt_ctrl.cancel(aid, self.student2)
        self.assertTrue(ok)
        # 候补自动转正
        wid = self.waitlist_ctrl.list_by_user(self.student1["uid"])[0]["wid"]
        self.assertEqual(self.waitlist_ctrl.dao.get_by_id(wid)["status"], WAIT_PROMOTED)
        # 学生1 收到通知，并生成一张待审核预约
        self.assertEqual(len(self.appt_ctrl.list_by_user(self.student1["uid"])), 1)
        self.assertGreater(self.msg_ctrl.unread_count(self.student1["uid"]), 0)
