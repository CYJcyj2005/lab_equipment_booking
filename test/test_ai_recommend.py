# -*- coding: utf-8 -*-
"""AI 智能推荐空闲时段单元测试。"""

import unittest
from datetime import datetime, timedelta

from utils.ai_recommend import recommend_slots


class TestAIRecommend(unittest.TestCase):
    def test_recommend_empty_day(self):
        day = datetime(2026, 10, 20)
        slots = recommend_slots([], day, 2)
        self.assertEqual(len(slots), 3)
        self.assertEqual(slots[0][0], day.replace(hour=8, minute=0))
        self.assertEqual(slots[0][1], day.replace(hour=10, minute=0))

    def test_recommend_skips_booked(self):
        day = datetime(2026, 10, 20)
        booked = [(day.replace(hour=8), day.replace(hour=10))]
        slots = recommend_slots(booked, day, 2)
        self.assertEqual(slots[0][0], day.replace(hour=10, minute=0))

    def test_recommend_respects_duration(self):
        day = datetime(2026, 10, 20)
        booked = [(day.replace(hour=8), day.replace(hour=21))]  # 仅剩 21-22 一小时
        slots = recommend_slots(booked, day, 2)
        self.assertTrue(all((s[1] - s[0]) >= timedelta(hours=2) for s in slots))
