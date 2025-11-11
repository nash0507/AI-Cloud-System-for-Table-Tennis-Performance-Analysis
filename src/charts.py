"""Matplotlib chart helpers for the Streamlit dashboard."""
from __future__ import annotations

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_stroke_distribution(df: pd.DataFrame):
    """顯示正拍與反拍的使用比例，協助教練判斷手型習慣。"""

    counts = df["stroke"].fillna("UNK").value_counts()
    fig, ax = plt.subplots(figsize=(5, 3))
    counts = counts.reindex(["F", "B", "UNK"]).fillna(0)
    ax.bar(counts.index, counts.values, color=["#ffb703", "#219ebc", "#8ecae6"])
    ax.set_title("正拍 / 反拍 使用比例")
    ax.set_ylabel("次數")
    ax.set_xlabel("手型")
    return fig


def _quadrant_grid_counts(df: pd.DataFrame) -> Tuple[np.ndarray, list]:
    quadrants = [f"Q{i}" for i in range(1, 10)]
    counts = df["landing_quadrant"].fillna("UNK").value_counts()
    matrix = np.zeros((3, 3), dtype=float)
    for idx, quadrant in enumerate(quadrants):
        row = idx // 3
        col = idx % 3
        matrix[row, col] = counts.get(quadrant, 0)
    return matrix, quadrants


def plot_landing_heatmap(df: pd.DataFrame):
    """落點 3x3 熱圖，觀察常見落點與弱點。"""

    matrix, quadrants = _quadrant_grid_counts(df)
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(matrix, cmap="Oranges")
    for row in range(3):
        for col in range(3):
            q = quadrants[row * 3 + col]
            ax.text(col, row, f"{q}\n{int(matrix[row, col])}", ha="center", va="center", color="black")
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(["1", "2", "3"])
    ax.set_yticklabels(["1", "2", "3"])
    ax.set_title("落點分布熱圖")
    fig.colorbar(im, ax=ax, shrink=0.7)
    return fig


def plot_rally_length(df: pd.DataFrame):
    """統計每一球的拍數分布，了解回合長度。"""

    rally_counts = df.groupby("rally_id").size()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(rally_counts, bins=range(1, int(rally_counts.max() if not rally_counts.empty else 1) + 2), color="#fb8500")
    ax.set_xlabel("拍數")
    ax.set_ylabel("回合數")
    ax.set_title("每球拍數分布（rally 長度）")
    return fig


def summarize_players(df: pd.DataFrame) -> pd.DataFrame:
    """彙整球員得失分與手型比例，提供教練快速檢視。"""

    summaries = []
    for player, g in df.groupby("player"):
        total_won = (g["outcome"] == "W").sum()
        total_lost = (g["outcome"] == "L").sum()
        total = len(g)
        forehand_ratio = (g["stroke"] == "F").sum() / total if total else 0.0
        backhand_ratio = (g["stroke"] == "B").sum() / total if total else 0.0
        avg_rally = g.groupby("rally_id").size().mean() if not g.empty else 0.0
        summaries.append(
            {
                "player": player,
                "total_points_won": total_won,
                "total_points_lost": total_lost,
                "forehand_ratio": round(forehand_ratio, 3),
                "backhand_ratio": round(backhand_ratio, 3),
                "avg_rally_length": round(avg_rally, 2) if not np.isnan(avg_rally) else 0.0,
            }
        )
    return pd.DataFrame(summaries)


__all__ = [
    "plot_stroke_distribution",
    "plot_landing_heatmap",
    "plot_rally_length",
    "summarize_players",
]
