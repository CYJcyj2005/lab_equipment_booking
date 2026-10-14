# -*- coding: utf-8 -*-
"""签到 + 门禁/电源联动单元测试。"""

from datetime import datetime, timedelta

from controller.sign_controller import SignController
from test.common import BaseTestCase
from utils.constants import SIGN_MANUAL


class TestSign(BaseTestCase):
    def test_sign_in_success_and_linkage(self):
        now = datetime.now()
        start = now + timedelta(minutes=1)
        end = start + timedelta(hours=2)
        ok, _ = self.appt_ctrl.submit_appointment(self.student1["uid"], self.dev1["did"],
                                                  start, end)
        self.assertTrue(ok)
        aid = self.appt_ctrl.list_by_user(self.student1["uid"])[0]["aid"]
        self.appt_ctrl.audit(aid, 1, "", self.admin1)

        sc = SignController(self.db_path)
        ok, msg = sc.sign_in(self.student1["uid"], aid, SIGN_MANUAL)
        self.assertTrue(ok, msg)
        self.assertEqual(sc.iot.get_power(self.dev1["did"]), 1)

        # 重复签到被拒
        ok2, _ = sc.sign_in(self.student1["uid"], aid, SIGN_MANUAL)
        self.assertFalse(ok2)

    def test_sign_in_wrong_user_denied(self):
        now = datetime.now()
        start = now + timedelta(minutes=1)
        end = start + timedelta(hours=2)
        self.appt_ctrl.submit_appointment(self.student1["uid"], self.dev1["did"], start, end)
        aid = self.appt_ctrl.list_by_user(self.student1["uid"])[0]["aid"]
        self.appt_ctrl.audit(aid, 1, "", self.admin1)
        sc = SignController(self.db_path)
        ok, _ = sc.sign_in(self.student2["uid"], aid, SIGN_MANUAL)
        self.assertFalse(ok)
