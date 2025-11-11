# AI Cloud System for Table Tennis Performance Analysis

桌球選手比賽狀態與弱點雲端分析系統提供教練一個整合式平台，完成比賽影片標註、數據視覺化以及訓練建議產生。此 MVP 包含 Streamlit 網頁介面與基本的 AI 輔助建議，協助教練快速找出選手弱點並規劃訓練方向。

## Tech Stack
- Python 3
- Streamlit
- OpenCV
- pandas / numpy
- matplotlib
- (Optional) MediaPipe for pose-based suggestions

## Project Structure
```
table-tennis-ai-cloud/
├─ app.py                 # Streamlit 單頁應用，含三個主要分頁
├─ src/
│  ├─ utils.py            # Event dataclass、I/O 與象限工具
│  ├─ analyzer.py         # 影格擷取、格線疊加、AI 建議
│  ├─ charts.py           # Matplotlib 視覺化
│  └─ rules.py            # 指標計算與訓練建議邏輯
├─ data/
│  ├─ samples/            # 範例影片存放 (可自行加入)
│  ├─ labels/             # 標註檔案資料夾
│  └─ uploads/            # 使用者上傳影片暫存
├─ reports/               # 匯出的 CSV 與 Markdown 建議卡
├─ requirements.txt
└─ README.md
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Usage Workflow
1. 啟動 Streamlit 後，從側邊欄上傳桌球比賽影片 (MP4)。
2. 進入「標註 Annotation」分頁：
   - 利用影格導覽按鈕跳轉影格，並在影像上點擊落點 (Q1~Q9)。
   - 透過按鈕快速標記正拍/反拍/發球/失誤等事件，AI 建議可協助預填手型與落點。
   - 事件會即時存入 Session 並顯示最近 10 筆資料。
3. 切換到「儀表板 Dashboard」分頁：
   - 檢視正拍/反拍使用比例、落點熱圖、rally 拍數分佈等圖表。
   - 比較不同球員的得失分與平均回合長度。
4. 前往「建議卡 Recommendations」分頁：
   - 系統依據規則運算出失誤率、發球短球比例等指標。
   - 自動生成中文訓練建議卡，並可匯出為 Markdown 檔案。
5. 側邊欄可將標註資料匯出為 CSV，方便進一步分析或備份。

## Interpreting the Analytics
- **正拍 / 反拍 使用比例**：顯示選手不同手型的出手偏好，可判斷手型是否平衡。
- **落點分布熱圖**：協助教練觀察選手與對手常用的落點區域，規劃戰術與訓練重點。
- **每球拍數分布**：回合長度揭露選手相持能力與進攻效率。
- **訓練建議卡**：透過簡單規則，快速指出失誤率偏高或發球變化不足等問題，提供具體練習方向。

歡迎擴充更進階的電腦視覺模型、資料庫或自動偵測模組，打造更完整的桌球戰術分析平台。
