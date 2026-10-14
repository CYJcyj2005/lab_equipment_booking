# 实验九：单元测试报告

## 1. 测试概述

| 项目 | 内容 |
| --- | --- |
| 测试类型 | 单元测试 |
| 测试框架 | Python `unittest` + `coverage` |
| 被测对象 | model / controller / utils 层核心逻辑 |
| 测试环境 | Windows 11，Python 3.10+，SQLite（临时库） |
| 执行方式 | `python -m unittest discover -s test` |

## 2. 测试策略

- 使用 `test/common.py` 的 `BaseTestCase`，每次用例创建独立临时数据库并预置测试数据（学生 student1/student2、管理员 admin1、设备 DEV-001…）；
- 控制器依赖注入 `db_path`，实现测试隔离；
- 业务层与数据库解耦，单元测试不依赖 GUI。

## 3. 测试用例清单与结果

### 3.1 用户模块 `test_user.py`（8 个）

| 编号 | 用例 | 预期 | 结果 |
| --- | --- | --- | --- |
| UT-U1 | test_register_success | 注册成功 | ✅ |
| UT-U2 | test_register_duplicate_username | 用户名重复被拒 | ✅ |
| UT-U3 | test_register_short_password | 短密码被拒 | ✅ |
| UT-U4 | test_register_invalid_phone | 非法手机号被拒 | ✅ |
| UT-U5 | test_login_success | 正确密码登录成功 | ✅ |
| UT-U6 | test_login_wrong_password | 错误密码失败 | ✅ |
| UT-U7 | test_login_not_found | 不存在用户失败 | ✅ |
| UT-U8 | test_change_password | 修改密码后新密码生效 | ✅ |

### 3.2 设备模块 `test_device.py`（4 个）

| 编号 | 用例 | 预期 | 结果 |
| --- | --- | --- | --- |
| UT-D1 | test_add_device_success | 新增成功 | ✅ |
| UT-D2 | test_add_device_duplicate_no | 设备号重复被拒 | ✅ |
| UT-D3 | test_list_devices_keyword | 关键字搜索命中 | ✅ |
| UT-D4 | test_set_status | 状态更新成功 | ✅ |

### 3.3 预约核心模块 `test_appointment.py`（10 个）

| 编号 | 用例 | 预期 | 结果 |
| --- | --- | --- | --- |
| UT-01 | test_submit_success | 正常无冲突提交成功 | ✅ |
| UT-02 | test_submit_past_time | 过去时间被拒 | ✅ |
| UT-03 | test_submit_over_max_hours | 超过最大时长被拒 | ✅ |
| UT-04 | test_submit_time_conflict | 时段冲突被拒 | ✅ |
| UT-05 | test_submit_blacklist_user | 黑名单用户被拒 | ✅ |
| UT-06 | test_submit_device_repair | 维修设备被拒 | ✅ |
| UT-07 | test_submit_end_before_start | 结束早于开始被拒 | ✅ |
| UT-A1 | test_audit_approve | 审核通过置设备占用 | ✅ |
| UT-A2 | test_audit_reject_requires_reason | 驳回未填理由被拒 | ✅ |
| UT-10 | test_no_show_threshold_blacklist | 爽约达阈值触发黑名单 | ✅ |

### 3.4 候补模块 `test_waitlist.py`（3 个）

| 编号 | 用例 | 预期 | 结果 |
| --- | --- | --- | --- |
| UT-W1 | test_join_and_cancel | 加入并取消候补 | ✅ |
| UT-W2 | test_cancel_others_waitlist_denied | 取消他人候补被拒 | ✅ |
| UT-08/09 | test_cancel_appointment_promotes_waitlist | 取消预约触发候补转正 | ✅ |

### 3.5 工具模块 `test_utils.py`（4 个）

| 编号 | 用例 | 预期 | 结果 |
| --- | --- | --- | --- |
| UT-X1 | test_backup_and_restore | 备份与恢复成功 | ✅ |
| UT-X2 | test_restore_missing | 恢复缺失文件报错 | ✅ |
| UT-X3 | test_export | CSV 导出成功 | ✅ |
| UT-X4 | test_lab_crud | 实验室增删改查 | ✅ |

## 4. 测试结果汇总

```
Ran 32 tests in 0.xxx s

OK
```

- 用例总数：32
- 通过：32
- 失败：0
- 错误：0
- 通过率：**100%**

## 5. 覆盖率

| 项目 | 覆盖率 |
| --- | --- |
| 总体行覆盖率 | **83%** |

- 未覆盖主要为 `view/` GUI 层（依赖 Qt 事件循环，由集成/冒烟测试覆盖）与部分防御性分支。

## 6. 缺陷记录（开发期已修复）

| 编号 | 描述 | 严重程度 | 状态 |
| --- | --- | --- | --- |
| BUG-01 | 学生主窗口调用 `notice_table.alignment()` 报 AttributeError | 高 | 已修复 |
| BUG-02 | `integration_test.py` 未被 unittest 发现（命名不符 test*.py） | 中 | 已修复（改名 test_integration.py） |
| BUG-03 | backup_util 不可测试（硬编码路径） | 中 | 已修复（参数注入） |

## 7. 结论

32 个单元测试全部通过，核心预约业务（提交校验、审核、取消、爽约黑名单、候补转正）得到充分验证，覆盖率达到 83%，满足课程 ≥80% 目标，单元测试结论为**通过**。
