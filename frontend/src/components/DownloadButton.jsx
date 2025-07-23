import React from 'react';
import * as XLSX from 'xlsx';

export default function DownloadButton({ sourceData, selections }) {
  const handleDownload = () => {
    // 將原始上傳資料與使用者選擇結果合併
    const sheetData = sourceData.map((row, i) => {
      const sel = selections[i] || {};
      return {
        // 原始所有欄位
        ...row,
        // 新增三個選擇欄位
        選擇名稱: sel.name || '',
        選擇單位: sel.unit || '',
        選擇碳排: sel.carbon || '',
      };
    });

    // 轉為 worksheet & workbook
    const ws = XLSX.utils.json_to_sheet(sheetData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '結果');

    // 觸發下載
    XLSX.writeFile(wb, 'matched_result.xlsx');
  };

  return (
    <button onClick={handleDownload}>
      下載結果 Excel
    </button>
  );
}