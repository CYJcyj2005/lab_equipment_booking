# -*- coding: utf-8 -*-
"""门禁/电源 + 物联网实时指标单元测试。"""

from controller.iot_controller import IoTController
from test.common import BaseTestCase


class TestIoT(BaseTestCase):
    def test_door_power(self):
        iot = IoTController(self.db_path)
        iot.set_door(1, True)
        self.assertEqual(iot.get_door(1), 1)
        iot.set_power(1, True)
        self.assertEqual(iot.get_power(1), 1)
        iot.set_power(1, False)
        self.assertEqual(iot.get_power(1), 0)

    def test_metrics(self):
        iot = IoTController(self.db_path)
        iot.refresh_metrics()
        metrics = iot.get_metrics()
        self.assertTrue(metrics)
        self.assertIn("dev_name", metrics[0])
