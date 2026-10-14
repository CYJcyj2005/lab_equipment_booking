# -*- coding: utf-8 -*-
"""人脸识别工具：注册 / 比对人脸，缺库或无摄像头时优雅降级为手动签到。"""

import os

from config import BASE_DIR

FACE_DIR = os.path.join(BASE_DIR, "data", "faces")

try:
    import cv2  # noqa: F401
    import face_recognition  # noqa: F401
    _FACE_OK = True
except ImportError:  # 缺依赖（如 Windows 上装不上 dlib）则降级
    cv2 = None
    face_recognition = None
    _FACE_OK = False


def face_available() -> bool:
    """人脸识别库是否可用。"""
    return _FACE_OK


def _face_file(uid: int) -> str:
    return os.path.join(FACE_DIR, f"{uid}.jpg")


def register_face(uid: int, image_bytes: bytes) -> bool:
    """保存用户人脸照片，返回是否成功。"""
    if not _FACE_OK:
        return False
    os.makedirs(FACE_DIR, exist_ok=True)
    with open(_face_file(uid), "wb") as f:
        f.write(image_bytes)
    return True


def has_face(uid: int) -> bool:
    return os.path.exists(_face_file(uid))


def capture_frame():
    """从默认摄像头抓取一帧（BGR），失败或不可用返回 None。"""
    if not _FACE_OK:
        return None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ok, frame = cap.read()
        cap.release()
        return frame if ok else None
    except Exception:
        return None


def verify_face(uid: int, frame) -> bool | None:
    """比对当前帧与已注册人脸。None 表示无法识别（触发手动签到回退）。"""
    if not _FACE_OK or frame is None:
        return None
    path = _face_file(uid)
    if not os.path.exists(path):
        return False
    try:
        known = face_recognition.load_image_file(path)
        known_enc = face_recognition.face_encodings(known)
        if not known_enc:
            return False
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb)
        if not locs:
            return False
        enc = face_recognition.face_encodings(rgb, locs)[0]
        return bool(face_recognition.compare_faces(known_enc, enc, tolerance=0.5)[0])
    except Exception:
        return False
