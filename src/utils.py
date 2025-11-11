"""Utility functions for table tennis annotation workflow."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

import pandas as pd


@dataclass
class Event:
    """描述單一球拍事件的資料結構 (table tennis event)."""

    rally_id: int
    frame: int
    event: str
    player: str
    stroke: str
    serve: str
    landing_quadrant: str
    outcome: str
    note: str = ""


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
LABEL_DIR = DATA_DIR / "labels"
UPLOAD_DIR = DATA_DIR / "uploads"


def ensure_dirs() -> None:
    """確保標註結果與報表的資料夾存在。"""

    for directory in (DATA_DIR, REPORT_DIR, LABEL_DIR, UPLOAD_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def save_events_to_csv(events: List[Event], out_csv: str) -> None:
    """將標註事件列表存成 CSV 供教練後續分析。"""

    df = pd.DataFrame([asdict(e) for e in events])
    if df.empty:
        df = pd.DataFrame(columns=[
            "rally_id",
            "frame",
            "event",
            "player",
            "stroke",
            "serve",
            "landing_quadrant",
            "outcome",
            "note",
        ])
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def load_events_from_csv(csv_path: str) -> List[Event]:
    """由 CSV 讀取標註事件，方便重複編輯。"""

    path = Path(csv_path)
    if not path.exists():
        return []
    df = pd.read_csv(path)
    events: List[Event] = []
    for row in df.to_dict(orient="records"):
        events.append(
            Event(
                rally_id=int(row.get("rally_id", 0)),
                frame=int(row.get("frame", 0)),
                event=str(row.get("event", "")),
                player=str(row.get("player", "")),
                stroke=str(row.get("stroke", "UNK")),
                serve=str(row.get("serve", "UNK")),
                landing_quadrant=str(row.get("landing_quadrant", "UNK")),
                outcome=str(row.get("outcome", "ongoing")),
                note=str(row.get("note", "")),
            )
        )
    return events


def map_quadrant(x: int, y: int, frame_shape, grid: str = "3x3") -> str:
    """將影像座標轉換為落點象限，預設為 3x3 棋盤。"""

    if grid != "3x3":
        return "UNK"
    height, width = frame_shape[:2]
    if width == 0 or height == 0:
        return "UNK"

    cell_w = width / 3
    cell_h = height / 3

    col = min(int(x // cell_w), 2)
    row = min(int(y // cell_h), 2)

    quadrant_index = row * 3 + col + 1
    return f"Q{quadrant_index}"


__all__ = [
    "Event",
    "ensure_dirs",
    "save_events_to_csv",
    "load_events_from_csv",
    "map_quadrant",
    "BASE_DIR",
    "DATA_DIR",
    "REPORT_DIR",
    "LABEL_DIR",
    "UPLOAD_DIR",
]
