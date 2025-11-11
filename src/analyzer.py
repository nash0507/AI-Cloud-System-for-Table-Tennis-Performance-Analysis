"""Video frame utilities and lightweight AI suggestions."""
from __future__ import annotations

import math
from typing import Dict, Optional

import cv2
import numpy as np

from .utils import map_quadrant

try:  # Optional MediaPipe support
    import mediapipe as mp

    _MP_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    mp = None  # type: ignore
    _MP_AVAILABLE = False


def get_frame(video_path: str, frame_index: int) -> Optional[np.ndarray]:
    """Load a specific frame from the video using OpenCV."""

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    success, frame = cap.read()
    cap.release()
    if not success:
        return None
    return frame


def draw_overlay(frame_bgr: np.ndarray, grid: str = "3x3") -> np.ndarray:
    """Draw a simple reference grid on the frame to guide landing annotation."""

    overlay = frame_bgr.copy()
    height, width = overlay.shape[:2]
    if grid == "3x3":
        step_x = width // 3
        step_y = height // 3
        color = (255, 255, 255)
        thickness = 1
        for i in range(1, 3):
            cv2.line(overlay, (i * step_x, 0), (i * step_x, height), color, thickness)
            cv2.line(overlay, (0, i * step_y), (width, i * step_y), color, thickness)
        # 標記 Q1..Q9 幫助教練理解座標系統
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        for row in range(3):
            for col in range(3):
                quadrant = f"Q{row * 3 + col + 1}"
                text_pos = (col * step_x + 10, row * step_y + 25)
                cv2.putText(overlay, quadrant, text_pos, font, font_scale, color, 1, cv2.LINE_AA)
    return overlay


def click_to_quadrant(x: int, y: int, frame_shape, grid: str = "3x3") -> str:
    """Shared helper to map click coordinates to quadrant names."""

    return map_quadrant(x, y, frame_shape, grid=grid)


_DEF_FALLBACK_SUGGESTION: Dict[str, object] = {
    "stroke_suggest": "UNK",
    "landing_suggest": "UNK",
    "is_serve": False,
}


def _heuristic_suggestion(frame_bgr: np.ndarray) -> Dict[str, object]:
    """Fallback heuristic when MediaPipe is unavailable."""

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    mean_intensity = float(gray.mean())
    # 簡單亮度判斷：亮度偏高時假設是正拍，否則反拍，僅作示意。
    stroke = "F" if mean_intensity > 110 else "B"
    # 使用邊緣強度估計是否為發球：邊緣少表示球未開打。
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = edges.mean() / 255.0
    is_serve = edge_ratio < 0.05

    h, w = gray.shape
    landing = map_quadrant(w // 2, h // 2, gray.shape)
    return {
        "stroke_suggest": stroke,
        "landing_suggest": landing,
        "is_serve": is_serve,
    }


def _mediapipe_suggestion(frame_bgr: np.ndarray) -> Dict[str, object]:
    """Very light-weight MediaPipe pose based suggestion."""

    if not _MP_AVAILABLE or mp is None:
        return _DEF_FALLBACK_SUGGESTION

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pose = mp.solutions.pose.Pose(static_image_mode=True)
    results = pose.process(frame_rgb)
    pose.close()
    if not results.pose_landmarks:
        return _DEF_FALLBACK_SUGGESTION

    # 根據手腕高度估計擊球方式
    landmarks = results.pose_landmarks.landmark
    left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value]
    right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value]

    stroke = "F"
    if left_wrist.visibility > right_wrist.visibility + 0.1:
        stroke = "B"
    elif right_wrist.visibility > left_wrist.visibility + 0.1:
        stroke = "F"
    else:
        stroke = "UNK"

    # 根據球員身體中心估計落點位置 (僅供參考)
    mid_x = (left_wrist.x + right_wrist.x) / 2
    mid_y = (left_wrist.y + right_wrist.y) / 2
    h, w = frame_rgb.shape[:2]
    landing = map_quadrant(int(mid_x * w), int(mid_y * h), frame_rgb.shape)

    # 使用膝蓋角度估計是否發球 (姿勢較低代表發球準備)
    left_knee = landmarks[mp.solutions.pose.PoseLandmark.LEFT_KNEE.value]
    right_knee = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value]
    hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value]
    knee_angle = math.degrees(
        math.atan2(left_knee.y - hip.y, left_knee.x - hip.x)
        + math.atan2(right_knee.y - hip.y, right_knee.x - hip.x)
    )
    is_serve = knee_angle < -0.5

    return {
        "stroke_suggest": stroke,
        "landing_suggest": landing,
        "is_serve": is_serve,
    }


def suggest_labels(frame_bgr: np.ndarray) -> Dict[str, object]:
    """Return AI suggestions for annotation, never raising an exception."""

    if frame_bgr is None:
        return _DEF_FALLBACK_SUGGESTION
    try:
        if _MP_AVAILABLE:
            return _mediapipe_suggestion(frame_bgr)
        return _heuristic_suggestion(frame_bgr)
    except Exception:
        return _DEF_FALLBACK_SUGGESTION


__all__ = [
    "get_frame",
    "draw_overlay",
    "click_to_quadrant",
    "suggest_labels",
]
