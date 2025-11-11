from __future__ import annotations

from datetime import datetime
import random
from pathlib import Path
from typing import List, Optional

import cv2
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from src import analyzer, charts, rules
from src.utils import (
    Event,
    ensure_dirs,
    save_events_to_csv,
    BASE_DIR,
    REPORT_DIR,
    UPLOAD_DIR,
)


ensure_dirs()


def _init_session_state() -> None:
    st.session_state.setdefault("events", [])
    st.session_state.setdefault("current_rally", 1)
    st.session_state.setdefault("current_frame", 0)
    st.session_state.setdefault("total_frames", 0)
    st.session_state.setdefault("video_path", None)
    st.session_state.setdefault("uploaded_name", None)
    st.session_state.setdefault("selected_quadrant", "UNK")
    st.session_state.setdefault("last_click_coords", (None, None))
    st.session_state.setdefault("latest_recommendations", [])
    st.session_state.setdefault("pending_stroke", "UNK")
    st.session_state.setdefault("pending_serve_is_short", False)
    st.session_state.setdefault("note_text", "")


_init_session_state()


def _events_to_df(events: List[Event]) -> pd.DataFrame:
    return pd.DataFrame([e.__dict__ for e in events])


def _load_video(uploaded_file) -> Optional[str]:
    if not uploaded_file:
        return st.session_state.get("video_path")
    if uploaded_file.name == st.session_state.get("uploaded_name"):
        return st.session_state.get("video_path")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = Path(uploaded_file.name).suffix or ".mp4"
    safe_name = Path(uploaded_file.name).stem.replace(" ", "_")
    out_path = UPLOAD_DIR / f"{safe_name}_{timestamp}{suffix}"
    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    cap = cv2.VideoCapture(str(out_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    st.session_state["uploaded_name"] = uploaded_file.name
    st.session_state["video_path"] = str(out_path)
    st.session_state["current_frame"] = 0
    st.session_state["total_frames"] = total_frames
    return str(out_path)


def _generate_fake_events() -> List[Event]:
    random.seed(42)
    fake_events: List[Event] = []
    rally_id = 1
    for i in range(30):
        frame = i * 15
        stroke = random.choice(["F", "B"])
        serve = random.choice(["short", "long", "UNK"])
        landing = random.choice([f"Q{j}" for j in range(1, 10)])
        outcome = random.choice(["ongoing", "W", "L"])
        event = random.choice(["stroke", "serve", "error"])
        player = random.choice(["A", "B"])
        if event == "serve":
            stroke = "UNK"
        fake_events.append(
            Event(
                rally_id=rally_id,
                frame=frame,
                event=event,
                player=player,
                stroke=stroke,
                serve=serve,
                landing_quadrant=landing,
                outcome=outcome,
                note="synthetic",
            )
        )
        if outcome in {"W", "L"}:
            rally_id += 1
    return fake_events


st.set_page_config(page_title="AI Cloud System for Table Tennis Analysis", layout="wide")
st.title("🏓 AI Cloud System for Table Tennis Performance Analysis")
st.caption("桌球選手比賽狀態與弱點雲端分析系統")

sidebar = st.sidebar
sidebar.header("控制面板")

uploaded_video = sidebar.file_uploader("上傳比賽影片 (MP4)", type=["mp4", "mov", "mkv"])
current_player = sidebar.selectbox("目前標記球員", options=["A", "B", "對手"], index=0)
ai_enabled = sidebar.checkbox("啟用 AI 建議 (MediaPipe，如果可用)")

if sidebar.button("載入假資料"):
    st.session_state["events"] = _generate_fake_events()
    st.session_state["current_rally"] = 1
    st.session_state["latest_recommendations"] = []
    st.toast("已載入示範資料。")

if sidebar.button("清空當前標註"):
    st.session_state["events"] = []
    st.session_state["current_rally"] = 1
    st.session_state["latest_recommendations"] = []
    st.toast("標註已清空。")

video_path = _load_video(uploaded_video)

if sidebar.button("匯出 CSV"):
    if st.session_state["events"]:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(st.session_state.get("uploaded_name") or "manual").stem
        csv_path = REPORT_DIR / f"{base_name}_{ts}.csv"
        save_events_to_csv(st.session_state["events"], str(csv_path))
        sidebar.success(f"已儲存到 {csv_path.relative_to(BASE_DIR)}")
    else:
        sidebar.warning("目前沒有可匯出的標註。")

if sidebar.button("生成建議卡"):
    df = _events_to_df(st.session_state["events"])
    if df.empty:
        sidebar.warning("請先建立標註資料。")
    else:
        metrics = rules.build_metrics(df)
        st.session_state["latest_recommendations"] = rules.generate_recommendations(metrics)
        sidebar.success("已在建議卡分頁更新建議。")

annotation_tab, dashboard_tab, recommendation_tab = st.tabs([
    "標註 Annotation",
    "儀表板 Dashboard",
    "建議卡 Recommendations",
])

with annotation_tab:
    st.subheader("影片標註")
    if not video_path:
        st.info("請從左側上傳比賽影片或使用假資料。")
    else:
        total_frames = st.session_state.get("total_frames", 0)
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
        if col_nav1.button("-10 框"):
            st.session_state["current_frame"] = max(0, st.session_state["current_frame"] - 10)
        if col_nav2.button("-1 框"):
            st.session_state["current_frame"] = max(0, st.session_state["current_frame"] - 1)
        if col_nav3.button("+1 框"):
            st.session_state["current_frame"] = min(max(total_frames - 1, 0), st.session_state["current_frame"] + 1)
        if col_nav4.button("+10 框"):
            st.session_state["current_frame"] = min(max(total_frames - 1, 0), st.session_state["current_frame"] + 10)

        st.write(f"目前影格: {st.session_state['current_frame']} / {total_frames}")
        frame = analyzer.get_frame(video_path, st.session_state["current_frame"])
        if frame is None:
            st.error("無法讀取此影格，請確認影片檔案。")
        else:
            frame_with_overlay = analyzer.draw_overlay(frame)
            frame_rgb = cv2.cvtColor(frame_with_overlay, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            canvas = st_canvas(
                fill_color="rgba(255, 0, 0, 0.3)",
                stroke_width=0,
                background_image=img,
                height=frame_rgb.shape[0],
                width=frame_rgb.shape[1],
                drawing_mode="point",
                key=f"canvas_{st.session_state['current_frame']}",
                display_toolbar=False,
                update_streamlit=True,
            )
            if canvas.json_data and "objects" in canvas.json_data:
                last_obj = canvas.json_data["objects"][-1]
                x = int(last_obj.get("left", 0))
                y = int(last_obj.get("top", 0))
                quadrant = analyzer.click_to_quadrant(x, y, frame.shape)
                st.session_state["selected_quadrant"] = quadrant
                st.session_state["last_click_coords"] = (x, y)

            st.markdown(
                f"選取落點象限: **{st.session_state['selected_quadrant']}** (座標: {st.session_state['last_click_coords']})"
            )

            ai_suggestion = None
            if ai_enabled:
                ai_suggestion = analyzer.suggest_labels(frame)
                st.info(
                    f"AI 建議 -> 手型: {ai_suggestion['stroke_suggest']} | 落點: {ai_suggestion['landing_suggest']} | 發球: {ai_suggestion['is_serve']}"
                )
                if st.button("套用建議"):
                    st.session_state["selected_quadrant"] = ai_suggestion["landing_suggest"]
                    st.session_state["pending_stroke"] = ai_suggestion["stroke_suggest"]
                    st.session_state["pending_serve_is_short"] = bool(ai_suggestion["is_serve"])
                    st.toast("已套用建議，可立即記錄事件。")

            st.markdown("---")
            col_a, col_b = st.columns(2)
            serve_choice = col_a.selectbox("發球類型", options=["short", "long", "UNK"], key="serve_type")
            st.session_state["note_text"] = col_b.text_input("備註", value=st.session_state.get("note_text", ""))
            st.write("目前回合編號: ", st.session_state["current_rally"])

            def _record_event(event_type: str, stroke: str = "UNK", serve: str = "UNK", outcome: str = "ongoing"):
                event = Event(
                    rally_id=st.session_state["current_rally"],
                    frame=st.session_state["current_frame"],
                    event=event_type,
                    player=current_player,
                    stroke=stroke,
                    serve=serve,
                    landing_quadrant=st.session_state.get("selected_quadrant", "UNK"),
                    outcome=outcome,
                    note=st.session_state.get("note_text", ""),
                )
                st.session_state["events"].append(event)
                st.session_state["pending_stroke"] = "UNK"

            btn_row1 = st.columns(3)
            if btn_row1[0].button("標記正拍 (F)"):
                default_stroke = st.session_state.get("pending_stroke", "F")
                stroke_value = "F" if default_stroke == "UNK" else default_stroke
                _record_event("stroke", stroke=stroke_value)
                st.toast("已紀錄正拍事件")
            if btn_row1[1].button("標記反拍 (B)"):
                default_stroke = st.session_state.get("pending_stroke", "B")
                stroke_value = "B" if default_stroke == "UNK" else default_stroke
                _record_event("stroke", stroke=stroke_value)
                st.toast("已紀錄反拍事件")
            if btn_row1[2].button("標記發球 (S)"):
                serve_val = "short" if st.session_state.get("pending_serve_is_short") else serve_choice
                _record_event("serve", serve=serve_val)
                st.session_state["pending_serve_is_short"] = False
                st.toast("已紀錄發球事件")

            btn_row2 = st.columns(3)
            if btn_row2[0].button("標記失誤 (E)"):
                _record_event("error", outcome="L")
                st.toast("已紀錄失誤")
            if btn_row2[1].button("本分獲勝 (W)"):
                _record_event("result", outcome="W")
                st.toast("已紀錄得分")
            if btn_row2[2].button("本分失分 (L)"):
                _record_event("result", outcome="L")
                st.toast("已紀錄失分")

            if st.button("新一球 (rally +1)"):
                st.session_state["current_rally"] += 1
                st.session_state["selected_quadrant"] = "UNK"
                st.session_state["last_click_coords"] = (None, None)
                st.toast("已切換到下一球")

            st.markdown("### 最近 10 筆標註")
            df_events = _events_to_df(st.session_state["events"])
            if df_events.empty:
                st.write("尚無資料，請先標註事件。")
            else:
                st.dataframe(df_events.tail(10), use_container_width=True)

with dashboard_tab:
    st.subheader("對戰儀表板")
    df_events = _events_to_df(st.session_state["events"])
    if df_events.empty:
        st.info("尚未有標註資料，請先建立事件。")
    else:
        st.caption("這張圖顯示正拍/反拍的使用比例與偏好。")
        st.pyplot(charts.plot_stroke_distribution(df_events))

        st.caption("這張熱圖顯示常見的落點區域，教練可以觀察習慣。")
        st.pyplot(charts.plot_landing_heatmap(df_events))

        st.caption("這張直方圖說明每球拍數的分布，用於評估相持能力。")
        st.pyplot(charts.plot_rally_length(df_events))

        st.caption("球員整體摘要指標")
        st.dataframe(charts.summarize_players(df_events), use_container_width=True)

with recommendation_tab:
    st.subheader("訓練建議卡")
    df_events = _events_to_df(st.session_state["events"])
    if df_events.empty:
        st.info("請先建立標註資料以產生建議。")
    else:
        metrics = rules.build_metrics(df_events)
        st.markdown("#### 重要指標")
        st.table(pd.DataFrame(metrics, index=["value"]).T)

        recommendations = st.session_state.get("latest_recommendations") or rules.generate_recommendations(metrics)
        st.session_state["latest_recommendations"] = recommendations

        st.markdown("#### 建議內容")
        for rec in recommendations:
            st.markdown(f"> ✅ {rec}")

        if st.button("匯出為 Markdown"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            md_path = REPORT_DIR / f"weakness_cards_{ts}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join([f"- {rec}" for rec in recommendations])
            md_path.write_text(
                f"# 訓練建議卡\n\n生成時間: {datetime.now().isoformat()}\n\n" + content,
                encoding="utf-8",
            )
            st.success(f"已匯出 {md_path.relative_to(BASE_DIR)}")
