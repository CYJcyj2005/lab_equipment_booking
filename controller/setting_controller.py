# -*- coding: utf-8 -*-
"""系统参数控制器：读取 / 修改业务参数（预约最大时长、黑名单阈值等）。"""

from model.setting_model import SettingDAO


class SettingController:
    """系统参数业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = SettingDAO(db_path)

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.dao.get(key))
        except (TypeError, ValueError):
            return default

    def set(self, key: str, value) -> None:
        self.dao.set(key, value)

    def all(self) -> dict:
        return self.dao.all()
