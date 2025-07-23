import React, { useState } from 'react';
import * as XLSX from 'xlsx';

export default function FileUpload({ onResult }) {
  const [uploaded, setUploaded] = useState(false);
  const [fileName, setFileName] = useState('');

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setUploaded(true);

    const reader = new FileReader();
    reader.onload = async (evt) => {
      const wb = XLSX.read(evt.target.result, { type: 'binary' });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const data = XLSX.utils.sheet_to_json(sheet);
      // 只傳遞解析後的數據，不在這裡調用 API
      onResult(data);
    };
    reader.readAsArrayBuffer(file);
  };

  return (
    <div className="upload-section">
      <input
        id="file-upload"
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFile}
      />
      <label htmlFor="file-upload" className="upload-label">
        {uploaded ? '重新上傳檔案' : '上傳檔案'}
      </label>
      {uploaded && (
        <span className="file-name">
          已上傳: {fileName}
        </span>
      )}
    </div>
  );
}
