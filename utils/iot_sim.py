# -*- coding: utf-8 -*-
"""物联网设备实时状态模拟器（无真实硬件，用随机数据演示）。"""

import random


def random_metric() -> dict:
    """随机生成一条设备实时读数（电压/电流/温度/在线状态）。"""
    return {
        "voltage": round(random.uniform(210, 240), 1),
        "current": round(random.uniform(0.1, 5.0), 2),
        "temperature": round(random.uniform(20, 60), 1),
        "online": 1 if random.random() > 0.1 else 0,
    }
