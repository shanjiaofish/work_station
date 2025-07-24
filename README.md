# 📊 工作站管理系統 (Work Station Management System)

一個整合多功能的Web應用程式，包含材料碳排放比對、發票OCR辨識、Google地圖路線截圖以及碳係數查詢等功能。

## 🌟 主要功能

### 🧾 材料比對工具
- 上傳Excel材料清單，自動使用BM25算法進行智能匹配
- 與Supabase資料庫中的標準材料進行比對
- 提供碳排放數據和詳細的匹配結果
- 支援手動選擇和進階搜索功能

### 🔍 碳係數查詢系統
- 即時搜索材料碳排放係數資料庫
- 智能下拉選單，支援模糊搜索
- 顯示完整的係數記錄，包含年份、數據來源等資訊
- 響應式表格設計，支援行動裝置

### 📄 發票OCR工具
- 批量處理PDF格式的加油發票
- 自動辨識發票號碼、日期、種類、數量、地址等資訊
- 生成Excel報告，方便後續處理
- 支援拖拽上傳和即時預覽

### 🗺️ Google地圖截圖工具
- 輸入出發地和多個目的地，自動計算距離
- 產生高品質的路線圖截圖
- 提供Excel報告和圖片壓縮檔下載
- 適用於路線規劃和距離分析

## 🛠️ 技術架構

### 前端技術
- **React 19** - 現代化的UI框架
- **Vite** - 快速的建構工具
- **React Router** - 單頁面應用路由
- **Axios** - HTTP客戶端
- **React Select** - 下拉選單組件

### 後端技術
- **Flask** - Python Web框架
- **Google Maps API** - 地圖服務
- **Supabase** - 雲端資料庫
- **多種OCR引擎** - PaddleOCR, EasyOCR, CnOcr
- **MaterialCorrectSystem** - NestJS微服務

### 資料庫
- **Supabase PostgreSQL** - 材料碳排放係數資料庫
- 包含完整的材料名稱、單位、碳足跡、數據來源和年份資訊

## 📦 安裝與啟動

### 系統需求
- Node.js 18+ 
- Python 3.8+
- Google Maps API Key
- Supabase 專案設定

### 1. 克隆專案
```bash
git clone https://github.com/your-username/work-station.git
cd work-station
```

### 2. 啟動MaterialCorrectSystem後端
```bash
cd ../practice/MaterialCorrectSystem/backend
npm install
npm run start:dev
```
> 後端將在 http://localhost:3000 啟動

### 3. 啟動前端應用
```bash
cd frontend
npm install
npm run dev
```
> 前端將在 http://localhost:5173 啟動

### 4. 啟動Python後端 (可選)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
> Python後端將在 http://localhost:5000 啟動

## 🚀 使用指南

### 材料比對工具
1. 訪問 http://localhost:5173/carbon-match
2. 準備包含材料名稱的Excel檔案
3. 上傳檔案，系統將自動進行BM25匹配
4. 在結果頁面查看匹配結果和碳排放數據
5. 下載包含完整資訊的Excel報告

### 碳係數查詢系統
1. 訪問 http://localhost:5173/lookup
2. 在搜索框中輸入材料名稱
3. 從下拉選單中選擇目標材料
4. 查看該材料的所有係數記錄

### 發票OCR工具
1. 訪問 http://localhost:5173/ocr
2. 上傳包含多張發票的PDF檔案
3. 等待系統完成OCR辨識
4. 預覽辨識結果並下載Excel報告

### Google地圖工具
1. 訪問 http://localhost:5173/gmap
2. 輸入出發地和目的地列表
3. 點擊「產生路線圖」
4. 下載Excel報告和截圖壓縮檔

## 📁 專案結構

```
work_station/
├── frontend/                 # React前端應用
│   ├── src/
│   │   ├── components/       # 可重用組件
│   │   ├── pages/           # 頁面組件
│   │   ├── layout/          # 佈局組件
│   │   └── api/             # API配置
│   └── package.json
├── backend/                  # Flask後端
│   ├── app.py              # 主應用程式
│   ├── param.py            # OCR參數設定
│   ├── supabase_client.py  # 資料庫客戶端
│   ├── screenshots/        # 地圖截圖存放
│   ├── reports/           # OCR報告存放
│   └── uploads/           # 檔案上傳暫存
└── README.md
```

## 🔧 配置說明

### 環境變數
在 `backend/` 目錄下創建 `.env` 檔案：
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

### API配置
前端API配置位於 `frontend/src/api/config.js`：
```javascript
export const API_BASE = 'http://127.0.0.1:5000'
export const MATERIAL_API_BASE = 'http://localhost:3000'
```

## 📊 資料庫架構

### Materials Table (Supabase)
```sql
CREATE TABLE materials (
  material_id UUID PRIMARY KEY,
  material_name TEXT NOT NULL,
  declaration_unit TEXT,
  carbon_footprint DECIMAL,
  announcement_year INTEGER,
  data_source TEXT,
  created_time TIMESTAMP DEFAULT NOW()
);
```

## 🎨 設計特色

- **統一的UI設計** - 所有頁面採用一致的設計語言
- **響應式佈局** - 支援桌面、平板和手機設備
- **即時搜索** - 提供流暢的用戶體驗
- **錯誤處理** - 完善的錯誤提示和載入狀態
- **無障礙設計** - 符合網頁無障礙標準

## 🤝 貢獻指南

1. Fork 此專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權條款

此專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案


## 🙏 致謝

- Google Maps API 提供地圖服務
- Supabase 提供資料庫服務
- 各種開源OCR引擎的貢獻者
- React和相關生態系統的維護者

---

⭐ 如果這個專案對你有幫助，請給個星星支持一下！