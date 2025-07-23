// work_station/frontend/src/pages/GmapPage.jsx

import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE } from '../api/config';

function GmapPage() {
    const [origin, setOrigin] = useState('');
    const [destinations, setDestinations] = useState('');
    const [results, setResults] = useState([]);
    const [sessionId, setSessionId] = useState(null); // 新增 state 來儲存 session ID
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleRequest = async () => {
        if (!origin.trim() || !destinations.trim()) {
            setError('請務必填寫出發地與目的地！');
            return;
        }
        setIsLoading(true);
        setError('');
        setResults([]);
        setSessionId(null); // 重設 session ID

        try {
            const response = await axios.post(`${API_BASE}/api/gmap/process`, {
                origin,
                destinations,
            });
            setResults(response.data.results);
            setSessionId(response.data.session_id); // 儲存從後端拿到的 session ID
        } catch (err) {
            console.error('請求處理時發生錯誤:', err);
            const errorMessage = err.response?.data?.error || '發生未知的錯誤，請檢查後端日誌。';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };
    
    // --- 新增：下載按鈕的處理函式 ---
    const handleDownload = (fileType) => {
        if (!sessionId) return;
        // 直接讓瀏覽器導向下載連結，觸發下載
        window.location.href = `${API_BASE}/api/download/${fileType}/${sessionId}`;
    };

    return (
        <div className="gmap-page">
            <div className="container">
                <header className="header">
                    <h1><span role="img" aria-label="icon"></span> Google Map 路線截圖小工具</h1>
                    <p className="description">
                        輸入一個出發地和多個目的地，系統將自動計算距離並產生路線圖與報告。
                    </p>
                </header>

                <section className="input-section">
                    {/* ... (此處的輸入框與按鈕 JSX 維持不變) ... */}
                    <div className="form-group">
                        <label htmlFor="origin">出發地</label>
                        <input id="origin" type="text" value={origin} onChange={(e) => setOrigin(e.target.value)} placeholder="例如：台北市信義區市府路1號" className="form-control"/>
                    </div>
                    <div className="form-group">
                        <label htmlFor="destinations">目的地 (每行一個)</label>
                        <textarea id="destinations" value={destinations} onChange={(e) => setDestinations(e.target.value)} placeholder={`例如：\n桃園市中壢區中大路300號\n新竹市東區大學路1001號`} rows="5" className="form-control"/>
                    </div>
                    <button onClick={handleRequest} disabled={isLoading} className="btn btn-primary">{isLoading ? '處理中，請稍候...' : '產生路線圖'}</button>
                </section>

                {isLoading && <div className="loading-indicator">正在努力配對中，請稍候...</div>}
                {error && <div className="error-message">{error}</div>}

                {/* --- ↓↓↓ 核心修改處：當有結果時，顯示下載面板和結果 ↓↓↓ --- */}
                {results.length > 0 && sessionId && (
                    <>
                            <h3> </h3>
                            <div className="download-buttons">
                                <button onClick={() => handleDownload('excel')} className="btn btn-download excel">
                                    <span role="img" aria-label="excel icon">📄</span> 下載 Excel 報告
                                </button>
                                <button onClick={() => handleDownload('zip')} className="btn btn-download zip">
                                    <span role="img" aria-label="zip icon">📦</span> 下載圖片壓縮檔
                                </button>
                            </div>

                        <section className="results-section">
                            <h2>查詢結果預覽</h2>
                            <div className="results-grid">
                                {results.map((result, index) => (
                                    <div key={index} className="result-card">
                                        <h4>{result.destination}</h4>
                                        <p><strong>距離:</strong> {result.distance}</p>
                                        <a href={`${API_BASE}/${result.screenshot_url}`} target="_blank" rel="noopener noreferrer">
                                            <img src={`${API_BASE}/${result.screenshot_url}`} alt={`Map for ${result.destination}`} className="screenshot-preview"/>
                                        </a>
                                        <small>點擊圖片可看大圖</small>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </>
                )}
                {/* --- ↑↑↑ 核心修改結束 ↑↑↑ --- */}
            </div>
        </div>
    );
}

export default GmapPage;