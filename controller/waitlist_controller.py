# -*- coding: utf-8 -*-
"""候补队列控制器：加入候补、取消、取消预约后自动转正。"""

from datetime import datetime

from controller.log_controller import LogController
from controller.message_controller import MessageController
from model.appointment_model import AppointmentDAO
from model.device_model import DeviceDAO
from model.waitlist_model import WaitlistDAO
from utils.constants import (DEVICE_REPAIR, DEVICE_SCRAPPED, WAIT_CANCELLED,
                             WAIT_PROMOTED, WAIT_WAITING)
from utils.time_util import to_db_str


class WaitlistController:
    """候补队列业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = WaitlistDAO(db_path)
        self.appt_dao = AppointmentDAO(db_path)
        self.device_dao = DeviceDAO(db_path)
        self.msg = MessageController(db_path)
        self.log = LogController(db_path)

    def join(self, uid: int, did: int, start_time: datetime, end_time: datetime) -> tuple:
        """加入候补队列（目标时段已被占用时）。"""
        device = self.device_dao.get_by_id(did)
        if not device:
            return False, "设备不存在"
        if device["status"] in (DEVICE_REPAIR, DEVICE_SCRAPPED):
            return False, "设备当前不可预约"
        if start_time >= end_time:
            return False, "结束时间必须晚于开始时间"
        if start_time < datetime.now():
            return False, "不可候补过去时间"
        wid = self.dao.insert(uid, did, to_db_str(start_time), to_db_str(end_time))
        self.log.record(uid, f"加入候补队列 {wid}")
        return True, "已加入候补队列"

    def promote_first(self, did: int, start_time: str, end_time: str) -> bool:
        """某预约取消后调用：将最早候补者自动转正为「待审核」预约，并通知。"""
        w = self.dao.get_first_waiting(did, start_time, end_time)
        if not w:
            return False
        self.appt_dao.insert(w["uid"], did, start_time, end_time)
        self.dao.update_status(w["wid"], WAIT_PROMOTED)
        self.msg.send_message(w["uid"], "候补转正",
                              "您候补的设备时段已释放，已自动为您生成预约单，请等待管理员审核。")
        return True

    def cancel(self, wid: int, uid: int) -> tuple:
        """取消本人候补。"""
        w = self.dao.get_by_id(wid)
        if not w:
            return False, "候补记录不存在"
        if w["uid"] != uid:
            return False, "只能取消本人候补"
        if w["status"] != WAIT_WAITING:
            return False, "当前状态不可取消"
        self.dao.update_status(wid, WAIT_CANCELLED)
        return True, "已取消候补"

    def list_by_user(self, uid: int) -> list:
        return self.dao.list_by_user(uid)

    def list_all(self) -> list:
        return self.dao.list_all()
