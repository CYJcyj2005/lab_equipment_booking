# -*- coding: utf-8 -*-
"""测试公共夹具：构建内存仓库 + 各服务 + 示例数据。"""

from datetime import date

from lab_reservation import Equipment, EquipmentService, Lab, ReservationService, Role, UserService
from lab_reservation.repositories import InMemoryRepository


def make_services():
    """返回 (repo, user_svc, equip_svc, reserve_svc, student, admin) 六元组。"""
    repo = InMemoryRepository()
    user_svc = UserService(repo)
    equip_svc = EquipmentService(repo)
    reserve_svc = ReservationService(repo)

    student = user_svc.register("张三", "2022001", Role.STUDENT, "abc12345")
    admin = user_svc.register("王实验员", "T0001", Role.LAB_ADMIN, "admin123")

    repo.add_lab(Lab("L01", "网络实验室", "N515"))
    equip_svc.add(Equipment("E01", "示波器", "电子测量", "L01"))
    equip_svc.add(Equipment("E02", "信号发生器", "电子测量", "L01"))

    return repo, user_svc, equip_svc, reserve_svc, student, admin


D = date(2026, 10, 20)
