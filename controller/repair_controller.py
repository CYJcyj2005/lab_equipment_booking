# -*- coding: utf-8 -*-
"""故障报修控制器：提交报修、处理工单。"""

from controller.log_controller import LogController
from controller.message_controller import MessageController
from model.repair_model import RepairDAO
from utils.constants import REPAIR_STATUS_NAMES


class RepairController:
    """报修业务逻辑。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = RepairDAO(db_path)
        self.msg = MessageController(db_path)
        self.log = LogController(db_path)

    def submit_repair(self, uid: int, did: int, content: str) -> tuple:
        if not content.strip():
            return False, "故障描述不能为空"
        rid = self.dao.insert(uid, did, content.strip())
        self.log.record(uid, f"提交报修单 {rid}")
        return True, "报修已提交"

    def handle(self, rid: int, status: int, deal_msg: str = "",
               operator_uid: int | None = None) -> tuple:
        """处理报修：状态流转 待处理→维修中→已修复，并通知报修人。"""
        r = self.dao.get_by_id(rid)
        if not r:
            return False, "报修单不存在"
        self.dao.update_status(rid, status, deal_msg)
        name = REPAIR_STATUS_NAMES.get(status, "")
        self.msg.send_message(r["uid"], "报修进度更新",
                              f"您的报修单 {rid} 状态更新为：{name}")
        self.log.record(operator_uid, f"处理报修单 {rid}")
        return True, "处理完成"

    def list_by_user(self, uid: int) -> list:
        return self.dao.list_by_user(uid)

    def list_all(self) -> list:
        return self.dao.list_all()
