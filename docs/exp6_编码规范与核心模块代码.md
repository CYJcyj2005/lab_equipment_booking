# 实验六：编码规范与核心模块代码

## 1. 编码规范

### 1.1 命名规范

| 对象 | 规范 | 示例 |
| --- | --- | --- |
| 模块/文件 | 小写下划线 | `appointment_controller.py` |
| 类名 | 大驼峰 | `AppointmentController` |
| 函数/方法 | 小写下划线 | `submit_appointment` |
| 常量 | 全大写 | `MAX_BOOKING_HOURS` |
| 数据库表 | 小写单数 | `appointment` |
| 数据库列 | 小写下划线 | `audit_status` |

### 1.2 文件组织

```
lab_equipment_booking/
├── main.py               # 程序入口
├── config.py             # 全局配置常量
├── db/                   # 建表 + BaseDAO
├── model/                # 各实体 DAO（数据访问）
├── controller/           # 业务控制层
├── view/                 # PyQt6 界面层
├── utils/                # 通用工具
├── test/                 # 单元 / 集成测试
└── docs/                 # 实验文档
```

### 1.3 编码约定

1. 文件头 `# -*- coding: utf-8 -*-`，Python 3.10+ 语法；
2. 每个类与核心方法编写 docstring，说明职责与返回值；
3. 业务层统一返回 `(bool, str)` 元组，`bool` 表示成功与否，`str` 为提示消息；
4. View 层不得直接操作数据库，必须经 Controller；
5. 数据库操作统一封装在 BaseDAO，使用 `with closing(conn)` 保证连接关闭；
6. 密码使用 bcrypt，禁止明文存储；
7. 时间统一以 `%Y-%m-%d %H:%M:%S` 字符串入库，`parse_dt` 解析。

## 2. 核心模块代码

### 2.1 预约核心控制器 `appointment_controller.py`

```python
# -*- coding: utf-8 -*-
"""预约核心控制器：提交、审核、取消、爽约判定与黑名单。"""

from datetime import datetime

from config import BLACKLIST_THRESHOLD, CANCEL_DEADLINE_MINUTES, MAX_BOOKING_HOURS
from controller.log_controller import LogController
from controller.message_controller import MessageController
from controller.setting_controller import SettingController
from controller.waitlist_controller import WaitlistController
from model.appointment_model import AppointmentDAO
from model.device_model import DeviceDAO
from model.user_model import UserDAO
from utils.constants import (
    AUDIT_APPROVED, AUDIT_CANCELLED, AUDIT_COMPLETED, AUDIT_NO_SHOW,
    AUDIT_PENDING, AUDIT_REJECTED, DEVICE_IDLE, DEVICE_IN_USE,
    DEVICE_REPAIR, DEVICE_SCRAPPED, ROLE_LAB_ADMIN, ROLE_SUPER_ADMIN,
    USER_ACTIVE,
)
from utils.time_util import is_time_conflict, parse_dt, to_db_str

_ADMIN_ROLES = (ROLE_LAB_ADMIN, ROLE_SUPER_ADMIN)


class AppointmentController:
    """预约业务控制器 —— 系统核心模块。"""

    def __init__(self, db_path: str | None = None) -> None:
        self.dao = AppointmentDAO(db_path)
        self.device_dao = DeviceDAO(db_path)
        self.user_dao = UserDAO(db_path)
        self.msg = MessageController(db_path)
        self.log = LogController(db_path)
        self.waitlist = WaitlistController(db_path)
        self.setting = SettingController(db_path)

    @staticmethod
    def _parse_booked(rows: list) -> list:
        """把数据库时段字符串列表解析为 datetime 二元组列表。"""
        out = []
        for s, e in rows:
            ps, pe = parse_dt(s), parse_dt(e)
            if ps and pe:
                out.append((ps, pe))
        return out

    def _occupy_device(self, did: int) -> None:
        dev = self.device_dao.get_by_id(did)
        if dev and dev["status"] == DEVICE_IDLE:
            self.device_dao.set_status(did, DEVICE_IN_USE)

    def _release_device(self, did: int) -> None:
        dev = self.device_dao.get_by_id(did)
        if dev and dev["status"] == DEVICE_IN_USE:
            self.device_dao.set_status(did, DEVICE_IDLE)

    def submit_appointment(self, uid: int, did: int,
                           start_time: datetime, end_time: datetime) -> tuple:
        """提交预约申请，执行多重校验。返回 (是否成功, 消息)。"""
        now = datetime.now()
        if start_time >= end_time:
            return False, "结束时间必须晚于开始时间"
        if start_time < now:
            return False, "不可预约过去时间"
        hours = (end_time - start_time).total_seconds() / 3600
        max_hours = self.setting.get_int("max_booking_hours", MAX_BOOKING_HOURS)
        if hours > max_hours:
            return False, f"单次预约时长不可超过 {max_hours} 小时"

        device = self.device_dao.get_by_id(did)
        if not device:
            return False, "设备不存在"
        if device["status"] in (DEVICE_REPAIR, DEVICE_SCRAPPED):
            return False, "设备当前不可预约（维修/报废）"

        user = self.user_dao.get_by_id(uid)
        if not user:
            return False, "用户不存在"
        if user["status"] != USER_ACTIVE:
            return False, "账号已被禁用（黑名单），无法预约"

        booked = self._parse_booked(self.dao.get_valid_time_range_by_device(did))
        if is_time_conflict(start_time, end_time, booked):
            return False, "该时间段已被预约，可加入候补队列"

        aid = self.dao.insert(uid, did, to_db_str(start_time), to_db_str(end_time))
        self.log.record(uid, f"提交预约申请 {aid}")
        return True, "预约申请已提交，等待管理员审核"

    def audit(self, aid: int, audit_status: int, audit_msg: str,
              operator: dict) -> tuple:
        """审核通过 / 驳回。通过时复核冲突，驳回须填理由。"""
        r = self.dao.get_by_id(aid)
        if not r:
            return False, "预约单不存在"
        if r["audit_status"] != AUDIT_PENDING:
            return False, "仅「待审核」的预约可审核"
        if audit_status == AUDIT_REJECTED and not audit_msg.strip():
            return False, "驳回必须填写理由"

        if audit_status == AUDIT_APPROVED:
            start_dt, end_dt = parse_dt(r["start_time"]), parse_dt(r["end_time"])
            others = []
            for s, e in self.dao.get_valid_time_range_by_device(r["did"]):
                if s == r["start_time"] and e == r["end_time"]:
                    continue  # 排除自身
                ps, pe = parse_dt(s), parse_dt(e)
                if ps and pe:
                    others.append((ps, pe))
            if is_time_conflict(start_dt, end_dt, others):
                return False, "审核时发现时段冲突，请先处理冲突预约"

        self.dao.update_audit(aid, audit_status, audit_msg.strip())
        self.msg.send_message(r["uid"], "预约审核结果",
                              f"预约单 {aid} 已「{'通过' if audit_status == AUDIT_APPROVED else '驳回'}」"
                              + (f"：{audit_msg.strip()}" if audit_msg.strip() else ""))
        self.log.record(operator.get("uid"), f"审核预约单 {aid}")
        if audit_status == AUDIT_APPROVED:
            self._occupy_device(r["did"])
        return True, "审核完成"

    def cancel(self, aid: int, operator: dict) -> tuple:
        """取消预约。本人或管理员可取消；通过后取消触发候补转正。"""
        r = self.dao.get_by_id(aid)
        if not r:
            return False, "预约单不存在"
        if r["audit_status"] not in (AUDIT_PENDING, AUDIT_APPROVED):
            return False, "当前状态不可取消"
        is_owner = r["uid"] == operator.get("uid")
        is_admin = operator.get("role") in _ADMIN_ROLES
        if not (is_owner or is_admin):
            return False, "只能取消本人预约"

        if r["audit_status"] == AUDIT_APPROVED:
            st = parse_dt(r["start_time"])
            if st and (st - datetime.now()).total_seconds() < CANCEL_DEADLINE_MINUTES * 60:
                return False, f"距开始不足 {CANCEL_DEADLINE_MINUTES} 分钟，不可取消"

        self.dao.update_status(aid, AUDIT_CANCELLED)
        self.dao.execute("UPDATE appointment SET cancel_time = datetime('now', 'localtime') "
                         "WHERE aid = ?", (aid,))
        self._release_device(r["did"])
        self.log.record(operator.get("uid"), f"取消预约单 {aid}")
        self.waitlist.promote_first(r["did"], r["start_time"], r["end_time"])
        return True, "预约已取消"

    def mark_completed(self, aid: int, operator: dict) -> tuple:
        """标记已完成的预约，设备恢复空闲。"""
        r = self.dao.get_by_id(aid)
        if not r:
            return False, "预约单不存在"
        if r["audit_status"] != AUDIT_APPROVED:
            return False, "仅「已通过」的预约可标记完成"
        self.dao.update_status(aid, AUDIT_COMPLETED)
        self._release_device(r["did"])
        self.log.record(operator.get("uid"), f"标记预约单 {aid} 完成")
        return True, "已标记完成"

    def mark_no_show(self, aid: int, operator: dict) -> tuple:
        """标记爽约：爽约次数 +1，达到阈值则禁用账号（加入黑名单）。"""
        r = self.dao.get_by_id(aid)
        if not r:
            return False, "预约单不存在"
        if r["audit_status"] != AUDIT_APPROVED:
            return False, "仅「已通过」的预约可标记爽约"
        self.dao.update_status(aid, AUDIT_NO_SHOW)
        self._release_device(r["did"])

        user = self.user_dao.get_by_id(r["uid"])
        new_count = (user["blacklist_count"] or 0) + 1
        self.user_dao.set_blacklist_count(r["uid"], new_count)
        threshold = self.setting.get_int("blacklist_threshold", BLACKLIST_THRESHOLD)
        if new_count >= threshold:
            self.user_dao.set_status(r["uid"], 0)  # 禁用
            self.msg.send_message(r["uid"], "账号禁用",
                                  "累计爽约达到阈值，账号已被禁用（加入黑名单）。")
            tip = f"已标记爽约，累计 {new_count} 次，账号已加入黑名单"
        else:
            tip = f"已标记爽约，累计 {new_count} 次"
        self.log.record(operator.get("uid"), f"标记预约单 {aid} 爽约")
        return True, tip

    def get_by_id(self, aid: int) -> dict | None:
        return self.dao.get_by_id(aid)

    def list_by_user(self, uid: int) -> list:
        return self.dao.list_by_user(uid)

    def list_by_status(self, audit_status: int) -> list:
        return self.dao.list_by_status(audit_status)

    def list_all(self) -> list:
        return self.dao.list_all()
```

### 2.2 候补队列控制器 `waitlist_controller.py`

```python
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
```

## 3. 核心逻辑说明

### 3.1 多重校验链（提交预约）

`submit_appointment` 依次执行六重校验：

1. 结束时间 > 开始时间；
2. 开始时间不早于当前时间；
3. 单次时长 ≤ `max_booking_hours`（动态参数）；
4. 设备存在且非维修/报废；
5. 用户存在且账号正常（非黑名单）；
6. 与已通过预约无时段冲突（开区间算法）。

全部通过后写入 `appointment` 表并记录日志。

### 3.2 审核复核冲突

`audit` 通过时再次查询该设备「有效时段」，排除自身后做冲突检测，防止提交后、审核前出现的并发占用。

### 3.3 候补转正闭环

`cancel` 成功后调用 `promote_first`，精确匹配 `did + start_time + end_time` 下最早「等待中」候补，自动生成新「待审核」预约并推送站内消息，形成完整业务闭环。

### 3.4 爽约黑名单

`mark_no_show` 累加 `blacklist_count`，达到 `blacklist_threshold`（动态参数）时禁用账号并推送通知，实现黑名单的自动触发。
