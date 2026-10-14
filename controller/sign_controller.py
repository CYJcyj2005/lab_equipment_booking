# -*- coding: utf-8 -*-
"""签到控制器：人脸/手动签到，签到后联动门禁开门、设备通电。"""

from datetime import datetime, timedelta

from controller.iot_controller import IoTController
from controller.log_controller import LogController
from controller.message_controller import MessageController
from model.appointment_model import AppointmentDAO
from model.device_model import DeviceDAO
from model.sign_model import SignDAO
from utils.constants import AUDIT_APPROVED, SIGN_MANUAL
from utils.time_util import parse_dt


class SignController:
    """签到业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = SignDAO(db_path)
        self.appt_dao = AppointmentDAO(db_path)
        self.device_dao = DeviceDAO(db_path)
        self.msg = MessageController(db_path)
        self.log = LogController(db_path)
        self.iot = IoTController(db_path)

    def sign_in(self, uid: int, aid: int, method: str = SIGN_MANUAL) -> tuple:
        """签到：校验预约状态与时段，写签到记录，联动门禁/电源。返回 (是否成功, 消息)。"""
        r = self.appt_dao.get_by_id(aid)
        if not r:
            return False, "预约单不存在"
        if r["uid"] != uid:
            return False, "只能本人签到"
        if r["audit_status"] != AUDIT_APPROVED:
            return False, "仅「已通过」的预约可签到"
        st, et = parse_dt(r["start_time"]), parse_dt(r["end_time"])
        now = datetime.now()
        if not st or not et or now < st - timedelta(minutes=30) or now > et + timedelta(minutes=30):
            return False, "不在签到时段内（开始前 30 分钟至结束后 30 分钟）"
        if self.dao.has_signed(aid):
            return False, "该预约已签到"

        self.dao.insert(uid, aid, r["did"], method)
        dev = self.device_dao.get_by_id(r["did"])
        if dev and dev.get("lab_id"):
            self.iot.set_door(dev["lab_id"], True)
        self.iot.set_power(r["did"], True)
        self.msg.send_message(uid, "签到成功",
                              f"预约单 {aid} 签到成功，门禁已开、设备已通电。")
        self.log.record(uid, f"签到预约单 {aid}（{method}）")
        return True, "签到成功，门禁已开、设备已通电"

    def list_all(self) -> list:
        return self.dao.list_all()

    def list_by_user(self, uid: int) -> list:
        return self.dao.list_by_user(uid)
