# -*- coding: utf-8 -*-
"""设备台账控制器：CRUD、状态管理、浏览搜索。"""

from controller.log_controller import LogController
from model.device_model import DeviceDAO


class DeviceController:
    """设备管理业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = DeviceDAO(db_path)
        self.log = LogController(db_path)

    def add_device(self, dev_name: str, dev_no: str, category: str, lab_id: int,
                   spec: str = "", remark: str = "", total_count: int = 1) -> tuple:
        dev_name = (dev_name or "").strip()
        dev_no = (dev_no or "").strip()
        if not dev_name or not dev_no:
            return False, "设备名称和编号不能为空"
        if self.dao.get_by_no(dev_no):
            return False, "设备编号已存在"
        if total_count < 1:
            return False, "设备数量至少为 1"
        did = self.dao.create(dev_name, dev_no, category, lab_id, spec,
                              remark=remark, total_count=total_count,
                              qr_code=f"DEV:{dev_no}")
        self.log.record(None, f"新增设备：{dev_name}({dev_no})")
        return True, f"设备已添加（编号 {did}）"

    def list_devices(self, category: str = "", keyword: str = "",
                     status: int | None = None, campus_id: int | None = None) -> list:
        return self.dao.list_all(category, keyword, status, campus_id)

    def get_device(self, did: int) -> dict | None:
        return self.dao.get_by_id(did)

    def update_device(self, did: int, **fields) -> tuple:
        self.dao.update(did, **fields)
        return True, "设备信息已更新"

    def set_status(self, did: int, status: int) -> tuple:
        self.dao.set_status(did, status)
        return True, "设备状态已更新"
