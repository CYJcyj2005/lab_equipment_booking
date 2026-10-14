# 实验四：系统概要设计

## 1. MVC 分层架构

```
View 视图层（PyQt6 GUI）
    ↓ 调用接口，不直接操作数据库
Controller 业务控制层
    ↓ 调用 DAO
Model 模型 & DAO 层
    ↓
SQLite 数据库
```

**分层职责**：

| 层 | 目录 | 职责 |
| --- | --- | --- |
| View | view/ | PyQt6 界面，收集输入、展示结果，仅调用 Controller |
| Controller | controller/ | 业务规则、权限校验、状态机、跨模块编排 |
| Model | model/ + db/ | 数据实体与 SQL 存取（DAO），不含业务规则 |
| Utils | utils/ | 通用工具（加密、时间、校验、导出、备份） |

## 2. 核心模块（9 个）

1. 用户管理模块（UserController / UserDAO）
2. 设备管理模块（DeviceController / DeviceDAO）
3. 预约业务模块（AppointmentController / AppointmentDAO）—— **核心**
4. 故障报修模块（RepairController / RepairDAO）
5. 公告通知模块（NoticeController / NoticeDAO）
6. 统计报表模块（CSV 导出 + AppointmentDAO 联表查询）
7. 系统日志模块（LogController / SysLogDAO）
8. 候补队列模块（WaitlistController / WaitlistDAO）
9. 站内消息模块（MessageController / MessageDAO）

另有系统参数模块（SettingController / SettingDAO），支撑超管的参数动态配置。

## 3. 模块依赖约束

1. View 只依赖 Controller；
2. Controller 只依赖 Model-DAO 与 Utils；
3. Model-DAO 直接访问数据库；
4. 模块间通过函数接口交互，禁止跨模块访问内部变量。

## 4. 关键模块接口定义

> 接口返回统一约定 `(bool, str)`：`bool` 表示是否成功，`str` 为提示消息。

### 接口 1：预约提交

```python
AppointmentController.submit_appointment(uid, did, start_time, end_time) -> (bool, str)
```

- 输入：用户 ID、设备 ID、开始时间、结束时间；
- 输出：(是否成功, 消息)；
- 内部逻辑：时间合法性 → 时长校验 → 设备状态 → 黑名单 → 时间冲突检测 → 写入。

### 接口 2：获取设备列表

```python
DeviceController.list_devices(category="", keyword="", status=None) -> list[dict]
```

### 接口 3：预约审核

```python
AppointmentController.audit(aid, audit_status, audit_msg, operator) -> (bool, str)
```

### 接口 4：取消预约

```python
AppointmentController.cancel(aid, operator) -> (bool, str)
```

- 后置：状态置「已取消」，触发 `WaitlistController.promote_first()`。

### 接口 5：加入候补

```python
WaitlistController.join(uid, did, start_time, end_time) -> (bool, str)
```

### 接口 6：候补转正

```python
WaitlistController.promote_first(did, start_time, end_time) -> bool
```

### 接口 7：发送站内消息

```python
MessageController.send_message(receiver_uid, title, content) -> (bool, mid)
```

### 接口 8：数据库备份

```python
backup_database(db_path=None, backup_dir=None) -> (bool, str)
```

### 接口 9：登录

```python
UserController.login(username, password) -> (user_dict | None, msg)
```

## 5. 关键设计决策

| 决策点 | 方案 | 理由 |
| --- | --- | --- |
| 数据存储 | SQLite 文件库 | 免安装、可迁移，适配单机桌面应用 |
| 密码 | bcrypt | 带盐自适应，禁止明文 |
| 冲突检测 | 开区间 `start < other_end and other_start < end` | 首尾相接不算冲突，符合直觉 |
| 黑名单 | 爽约次数计数，达阈值禁用 | 阈值可配置（setting 表），灵活 |
| 候补转正 | 取消预约时自动取最早候补转正 | 形成预约完整闭环 |
| 跨模块调用 | 预约控制器依赖候补/消息控制器 | 单向依赖，避免循环引用 |
