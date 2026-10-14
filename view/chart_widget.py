# -*- coding: utf-8 -*-
"""统计图表组件：设备使用时长柱状图 + 预约状态占比饼图（matplotlib 嵌入 Qt）。"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from utils.constants import AUDIT_STATUS_NAMES
from utils.time_util import parse_dt

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    _MPL_OK = True
except Exception:  # 缺 matplotlib 或后端不可用时降级
    _MPL_OK = False


def build_stats_chart(appointments: list) -> QWidget:
    """根据预约记录构建统计图表组件。"""
    w = QWidget()
    v = QVBoxLayout(w)
    if not _MPL_OK:
        v.addWidget(QLabel("（未安装 matplotlib，无法显示图表）"))
        return w

    # 设备使用时长（已通过 + 已完成）
    usage: dict = {}
    status_count: dict = {}
    for a in appointments:
        st, et = parse_dt(a.get("start_time")), parse_dt(a.get("end_time"))
        if st and et and et > st:
            hours = (et - st).total_seconds() / 3600
            name = a.get("dev_name", "?")
            usage[name] = usage.get(name, 0) + hours
        sname = AUDIT_STATUS_NAMES.get(a.get("audit_status"), "未知")
        status_count[sname] = status_count.get(sname, 0) + 1

    fig = Figure(figsize=(8, 6), dpi=100)
    fig.subplots_adjust(hspace=0.5)

    ax1 = fig.add_subplot(211)
    if usage:
        names = list(usage.keys())
        ax1.bar(names, [usage[n] for n in names], color="#07C160")
        ax1.set_title("设备使用时长（小时）")
        ax1.tick_params(axis="x", rotation=20)
        ax1.set_ylabel("小时")
    else:
        ax1.text(0.5, 0.5, "暂无使用记录", ha="center", va="center")
        ax1.set_title("设备使用时长（小时）")

    ax2 = fig.add_subplot(212)
    if status_count:
        labels = list(status_count.keys())
        ax2.pie([status_count[k] for k in labels], labels=labels, autopct="%1.1f%%",
                colors=["#07C160", "#f5a623", "#fa5151", "#999999", "#4a90d9", "#8e8e93"])
        ax2.set_title("预约状态占比")
    else:
        ax2.text(0.5, 0.5, "暂无预约记录", ha="center", va="center")
        ax2.set_title("预约状态占比")

    canvas = FigureCanvas(fig)
    v.addWidget(canvas)
    return w
