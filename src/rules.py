"""Rule-based training recommendations for table tennis."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def _safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def build_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """計算球員各項數據，後續提供建議用。"""

    metrics: Dict[str, float] = {}
    total_strokes = (df["event"].isin(["stroke", "serve"])).sum()
    forehand_events = (df["stroke"] == "F").sum()
    backhand_events = (df["stroke"] == "B").sum()

    forehand_errors = ((df["stroke"] == "F") & (df["outcome"] == "L")).sum()
    backhand_errors = ((df["stroke"] == "B") & (df["outcome"] == "L")).sum()

    serves = df[df["event"] == "serve"]
    short_serves = (serves["serve"] == "short").sum()

    rally_sizes = df.groupby("rally_id").size()

    metrics["forehand_ratio"] = _safe_ratio(forehand_events, total_strokes)
    metrics["backhand_ratio"] = _safe_ratio(backhand_events, total_strokes)
    metrics["forehand_error_rate"] = _safe_ratio(forehand_errors, forehand_events)
    metrics["backhand_error_rate"] = _safe_ratio(backhand_errors, backhand_events)
    metrics["short_serve_ratio"] = _safe_ratio(short_serves, len(serves))
    metrics["rally_len_avg"] = float(rally_sizes.mean()) if not rally_sizes.empty else 0.0
    metrics["rally_len_p90"] = float(np.percentile(rally_sizes, 90)) if not rally_sizes.empty else 0.0

    return metrics


def generate_recommendations(metrics: Dict[str, float]) -> List[str]:
    """根據指標產生中文訓練建議，方便教練快速採取行動。"""

    recs: List[str] = []

    bh_err = metrics.get("backhand_error_rate", 0.0)
    fh_err = metrics.get("forehand_error_rate", 0.0)
    bh_ratio = metrics.get("backhand_ratio", 0.0)
    fh_ratio = metrics.get("forehand_ratio", 0.0)
    short_serve_ratio = metrics.get("short_serve_ratio", 0.0)
    rally_avg = metrics.get("rally_len_avg", 0.0)
    rally_p90 = metrics.get("rally_len_p90", 0.0)

    if bh_ratio > 0.35 and bh_err > fh_err * 1.2:
        recs.append(
            "【反拍穩定性】反拍出手比例偏高且失誤率明顯高於正拍，建議安排多球反拍封鎖與反拍對拉訓練。"
        )
    if fh_ratio < 0.3 and bh_ratio > 0.5:
        recs.append(
            "【手型平衡】正拍使用比例偏低，建議安排正拍主動進攻與快帶練習，避免過度依賴反拍。"
        )
    if short_serve_ratio < 0.3:
        recs.append(
            "【發球落點】短球比例偏低，容易被對手先上手，建議增加短球與假短真長的發球變化。"
        )
    if rally_avg < 4:
        recs.append(
            "【相持能力】多數回合在 4 拍內結束，建議加強中台多拍相持與過度球處理。"
        )
    if rally_p90 > 8:
        recs.append(
            "【耐力與體能】長回合比例不低，建議安排多球耐力訓練與步伐切換練習。"
        )
    if fh_err > 0.35:
        recs.append(
            "【正拍穩定】正拍失誤率偏高，建議檢查動作細節與引拍高度，安排穩定性專項練習。"
        )

    if not recs:
        recs.append("【整體評估】指標表現均衡，可維持現有訓練節奏並持續觀察。")

    return recs


__all__ = ["build_metrics", "generate_recommendations"]
