import React from 'react';
import * as XLSX from 'xlsx';

export default function DownloadButton({ data, filename = 'matched_result.xlsx' }) {
  const handleDownload = () => {
    // 資料已經在父組件中處理完成，直接使用
    const sheetData = data;

    // 轉為 worksheet & workbook
    const ws = XLSX.utils.json_to_sheet(sheetData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '結果');

    // 觸發下載，使用傳入的檔案名稱
    XLSX.writeFile(wb, filename);
  };

  return (
    <button onClick={handleDownload}>
      下載結果 Excel
    </button>
  );
}