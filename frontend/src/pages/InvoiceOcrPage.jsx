import React, { useState, useRef } from 'react';
import axios from 'axios';
import { API_BASE } from '../api/config';

function InvoiceOcrPage() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [downloadUrl, setDownloadUrl] = useState(null);
    const [ocrData, setOcrData] = useState([]); // 新增 state 來儲存結果資料
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file && file.type === "application/pdf") {
            setSelectedFile(file);
            setDownloadUrl(null);
            setOcrData([]); // 清除舊資料
            setError('');
        } else {
            setError('檔案格式錯誤，請僅上傳 PDF 檔案。');
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setError('請先選擇一個 PDF 檔案。');
            return;
        }

        setIsLoading(true);
        setError('');
        setDownloadUrl(null);
        setOcrData([]);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await axios.post(`${API_BASE}/api/ocr/process-pdf`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setDownloadUrl(response.data.download_url);
            setOcrData(response.data.data); // 儲存後端回傳的資料
        } catch (err) {
            console.error('上傳或處理時發生錯誤:', err);
            const errorMessage = err.response?.data?.error || '發生未知的錯誤，請檢查後端日誌。';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    // --- 拖曳檔案相關的處理函式 ---
    const handleDragEvents = (e, over) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(over);
    };
    const handleDrop = (e) => {
        handleDragEvents(e, false);
        const file = e.dataTransfer.files[0];
        if (file && file.type === "application/pdf") {
            setSelectedFile(file);
            setDownloadUrl(null);
            setOcrData([]);
            setError('');
        } else {
            setError('檔案格式錯誤，請僅上傳 PDF 檔案。');
        }
    };

    return (
        <div className="ocr-page">
            <div className="container">
                <header className="header">
                    <h1><span role="img" aria-label="invoice">📄</span> 加油發票 OCR 工具</h1>
                    <p className="description">
                        上傳包含多張加油發票的 PDF 檔案，系統將自動辨識並匯出成 Excel 報告。
                    </p>
                </header>

                <section 
                    className={`upload-box ${isDragOver ? 'drag-over' : ''}`}
                    onClick={() => fileInputRef.current.click()}
                    onDragEnter={(e) => handleDragEvents(e, true)}
                    onDragOver={(e) => handleDragEvents(e, true)}
                    onDragLeave={(e) => handleDragEvents(e, false)}
                    onDrop={handleDrop}
                >
                    <input
                        ref={fileInputRef}
                        id="pdf-upload"
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                    />
                    {selectedFile ? (
                        <div className="file-selected">
                            <span className="file-icon">📑</span>
                            <strong>已選擇檔案：</strong>
                            <p>{selectedFile.name}</p>
                            <small>點擊此處可重新選擇</small>
                        </div>
                    ) : (
                        <div className="upload-placeholder">
                            <span className="upload-icon">📤</span>
                            <p>點擊此處選擇檔案，或將檔案拖曳至此</p>
                            <small>僅支援 PDF 格式</small>
                        </div>
                    )}
                </section>

                <button
                    onClick={handleUpload}
                    disabled={isLoading || !selectedFile}
                    className="btn-process"
                >
                    {isLoading ? '辨識中，請耐心等候...' : '開始辨識'}
                </button>
                
                {error && <div className="error-message">{error}</div>}

                {/* --- ↓↓↓ 核心修改：當有結果時，顯示下載面板和預覽表格 ↓↓↓ --- */}
                {ocrData.length > 0 && (
                    <>
                        <div className="download-section">
                            <h3>🎉 辨識完成！</h3>
                            <a href={`${API_BASE}/${downloadUrl}`} className="btn-download-report" download>
                                <span role="img" aria-label="download">📥</span> 下載辨識報告 (Excel)
                            </a>
                        </div>

                        <section className="results-section">
                            <h2>辨識結果預覽</h2>
                            <div className="table-container">
                                <table className="ocr-results-table">
                                    <thead>
                                        <tr>
                                            <th>頁數/檔名</th>
                                            <th>發票號碼</th>
                                            <th>日期</th>
                                            <th>種類</th>
                                            <th>數量</th>
                                            <th>地址</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {ocrData.map((item, index) => (
                                            <tr key={index}>
                                                <td data-label="頁數/檔名">{item['頁數'] || 'N/A'}</td>
                                                <td data-label="發票號碼">{item['發票號碼'] || 'N/A'}</td>
                                                <td data-label="日期">{item['日期'] || 'N/A'}</td>
                                                <td data-label="種類">{item['種類'] || 'N/A'}</td>
                                                <td data-label="數量">{item['數量'] || 'N/A'}</td>
                                                <td data-label="地址">{item['地址'] || 'N/A'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    </>
                )}
            </div>
        </div>
    );
}

export default InvoiceOcrPage;
