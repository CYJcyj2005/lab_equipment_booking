# -*- coding: utf-8 -*-
"""CSV 报表导出（基于 pandas）。"""

import pandas as pd


def export_to_csv(rows: list, columns: list, headers: list, path: str) -> bool:
    """将 rows（dict 列表）按 columns 映射导出为 CSV，返回是否成功。

    :param rows: 数据行列表，每行是一个 dict
    :param columns: 需要导出的字段名列表
    :param headers: 与 columns 一一对应的表头中文名
    :param path: 输出文件路径
    """
    try:
        data = [{h: r.get(c, "") for c, h in zip(columns, headers)} for r in rows]
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return True
    except Exception:
        return False
