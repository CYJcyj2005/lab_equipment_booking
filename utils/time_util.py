# -*- coding: utf-8 -*-
"""时间工具：时段冲突检测、字符串与 datetime 互转。"""

from datetime import datetime
from typing import Iterable, Optional, Tuple


def is_time_conflict(start: datetime, end: datetime,
                     booked: Iterable[Tuple[datetime, datetime]]) -> bool:
    """判断 [start, end) 与已预约时段集合是否重叠。

    采用开区间比较，首尾相接（如 08:00-10:00 与 10:00-12:00）不算冲突。
    """
    for b_start, b_end in booked:
        if start < b_end and b_start < end:
            return True
    return False


def to_db_str(dt: datetime) -> str:
    """datetime 转数据库字符串。"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    """数据库字符串转 datetime，失败返回 None。"""
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def fmt(dt: Optional[datetime]) -> str:
    """统一时间显示格式。"""
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
