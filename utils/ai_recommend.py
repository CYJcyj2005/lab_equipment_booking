# -*- coding: utf-8 -*-
"""AI 智能推荐空闲时段（本地启发式算法，无需联网 / 密钥）。

算法思路：把目标日期已预约时段合并，在开放时段内找出满足时长要求的空闲空隙，
按 30 分钟粒度生成候选时段，按「越早越优先、缓冲越充裕越优先」打分，返回前 N 个。
"""

from datetime import datetime, timedelta
from typing import Iterable, List, Tuple


def _parse_hhmm(day: datetime, hhmm: str) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return day.replace(hour=h, minute=m, second=0, microsecond=0)


def recommend_slots(booked: Iterable[Tuple[datetime, datetime]],
                    day: datetime, duration_h: float,
                    open_time: str = "08:00", close_time: str = "22:00",
                    step_min: int = 30, top_n: int = 3) -> List[Tuple[datetime, datetime]]:
    """返回指定日期内推荐的空闲时段列表 [(start, end), ...]。"""
    day = day.replace(hour=0, minute=0, second=0, microsecond=0)
    open_dt = _parse_hhmm(day, open_time)
    close_dt = _parse_hhmm(day, close_time)
    duration = timedelta(hours=duration_h)

    # 过滤并合并当日已预约区间
    intervals: List[Tuple[datetime, datetime]] = []
    for b_start, b_end in booked:
        if b_start.date() == day.date() or b_end.date() == day.date():
            intervals.append((max(b_start, open_dt), min(b_end, close_dt)))
    intervals.sort()
    merged: List[Tuple[datetime, datetime]] = []
    for s, e in intervals:
        if s >= e:
            continue
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # 计算空闲空隙
    free: List[Tuple[datetime, datetime]] = []
    cursor = open_dt
    for s, e in merged:
        if cursor < s:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < close_dt:
        free.append((cursor, close_dt))

    # 生成候选并打分（越早越优先，缓冲越充裕越优先）
    step = timedelta(minutes=step_min)
    candidates: List[Tuple[float, float, datetime, datetime]] = []
    for fs, fe in free:
        if fe - fs < duration:
            continue
        s = fs
        while s + duration <= fe:
            hour = (s - open_dt).total_seconds() / 3600
            buffer = min((s - fs).total_seconds(), (fe - (s + duration)).total_seconds()) / 60
            candidates.append((hour, -buffer, s, s + duration))
            s += step

    candidates.sort(key=lambda c: (c[0], c[1]))
    return [(c[2], c[3]) for c in candidates[:top_n]]
