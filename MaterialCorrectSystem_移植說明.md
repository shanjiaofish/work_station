# MaterialCorrectSystem 移植到 CarbonMatchPage 和 CarbonMatchResultPage

## 🎯 移植完成概要

我已經成功將 MaterialCorrectSystem 的完整功能移植到您的現有網站中：

### 📄 **第一頁：CarbonMatchPage.jsx**
- **功能**：檔案上傳和初始匹配
- **特色**：
  - 支援 Excel (.xlsx/.xls) 檔案上傳
  - 自動使用 BM25 算法進行智能材料匹配
  - 美觀的 UI 設計，包含使用說明和格式要求
  - 錯誤處理和載入狀態顯示
  - 自動跳轉到結果頁面

### 📄 **第二頁：CarbonMatchResultPage.jsx**
- **功能**：結果展示、進階搜尋和選擇確認
- **特色**：
  - 雙模式搜尋：AI 推薦 vs 完整資料庫搜尋
  - React-Select 下拉選單，支援搜尋功能
  - 新增材料功能（彈窗表單）
  - Excel 結果下載
  - 響應式表格設計

## 🔧 **技術實現**

### API 配置
```javascript
// frontend/src/api/config.js
export const API_BASE = 'http://127.0.0.1:5000'
export const MATERIAL_API_BASE = 'http://localhost:3000' // MaterialCorrectSystem NestJS backend
```

### 主要依賴項
- `axios` - API 請求
- `react-select` - 進階下拉選單
- `xlsx` - Excel 檔案處理
- `react-router-dom` - 頁面導航

### 路由配置
```javascript
// App.jsx 中已包含
<Route path="carbon-match" element={<CarbonMatchPage />} />
<Route path="carbon-match-result" element={<CarbonMatchResultPage />} />
```

## 🚀 **使用流程**

1. **上傳檔案**：在 CarbonMatchPage 上傳包含材料名稱的 Excel 檔案
2. **自動匹配**：系統使用 BM25 算法自動匹配最相似的材料
3. **查看結果**：跳轉到 CarbonMatchResultPage 查看匹配結果
4. **進階搜尋**：點擊「更多搜尋」可從完整資料庫中搜尋
5. **新增材料**：可新增自定義材料到資料庫
6. **下載結果**：下載包含碳排放數據的完整 Excel 結果

## 📋 **所需後端服務**

### MaterialCorrectSystem NestJS Backend (Port 3000)
需要啟動 MaterialCorrectSystem 的 NestJS 後端服務：

```bash
cd C:/Users/Tim/Desktop/python/practice/MaterialCorrectSystem/backend
npm install
npm run start:dev
```

### API 端點
- `POST /materials/match-batch` - 批量材料匹配
- `GET /materials/all` - 獲取所有材料
- `POST /materials` - 新增材料

## 🎨 **UI 特色**

- **現代化設計**：使用內聯樣式，無需額外 CSS 檔案
- **響應式布局**：適配不同螢幕尺寸
- **直觀操作**：清晰的按鈕和狀態提示
- **錯誤處理**：友善的錯誤訊息和載入狀態

## 🔍 **核心功能對比**

| 功能 | MaterialCorrectSystem 原版 | 移植版本 |
|------|---------------------------|----------|
| 檔案上傳 | ✅ | ✅ |
| BM25 智能匹配 | ✅ | ✅ |
| 雙模式搜尋 | ✅ | ✅ |
| 新增材料 | ✅ | ✅ |
| Excel 下載 | ✅ | ✅ |
| 響應式設計 | ❌ | ✅ |
| 頁面導航 | ❌ | ✅ |

## 🎯 **測試建議**

1. 確保 NestJS 後端服務正在運行 (localhost:3000)
2. 準備測試用的 Excel 檔案（包含材料名稱欄位）
3. 訪問 `/carbon-match` 開始測試
4. 測試完整流程：上傳 → 匹配 → 選擇 → 下載

移植工作已完成，所有 MaterialCorrectSystem 的核心功能都已成功整合到您的網站中！
