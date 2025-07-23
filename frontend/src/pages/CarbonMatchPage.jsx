import React, { useState } from 'react';
import axios from 'axios';
import * as XLSX from 'xlsx';
import { useNavigate } from 'react-router-dom';
import { MATERIAL_API_BASE } from '../api/config';
import '../App.css';

function CarbonMatchPage() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [uploaded, setUploaded] = useState(false);
    const [fileName, setFileName] = useState('');
    const navigate = useNavigate();

    // 處理檔案上傳
    const handleFile = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setFileName(file.name);
        setUploaded(true);
        setIsLoading(true);
        setError('');

        try {
            const reader = new FileReader();
            reader.onload = async (evt) => {
                const wb = XLSX.read(evt.target.result, { type: 'binary' });
                const sheet = wb.Sheets[wb.SheetNames[0]];
                const data = XLSX.utils.sheet_to_json(sheet);
                
                // 提取材料名稱進行批量匹配
                const queries = data.map(row => row['材料名稱'] || row['name'] || row[Object.keys(row)[0]]);
                
                try {
                    // 設定 5 秒超時
                    const response = await axios.post(`${MATERIAL_API_BASE}/materials/match-batch`, queries, {
                        timeout: 5000
                    });
                    
                    // 跳轉到結果頁面，帶上原始數據和匹配結果
                    navigate('/carbon-match-result', {
                        state: {
                            sourceData: data,
                            matchResults: response.data
                        }
                    });
                } catch (apiError) {
                    console.error('API 調用失敗:', apiError);
                    
                    // 如果 API 失敗，創建空的匹配結果，讓用戶可以手動選擇
                    const emptyMatchResults = queries.map(query => ({
                        query: query,
                        matches: [],
                        default: 0
                    }));
                    
                    navigate('/carbon-match-result', {
                        state: {
                            sourceData: data,
                            matchResults: emptyMatchResults,
                            apiError: true
                        }
                    });
                }
            };
            reader.readAsArrayBuffer(file);
        } catch (err) {
            console.error('處理檔案時發生錯誤:', err);
            setError('檔案處理失敗，請檢查檔案格式是否正確。');
            setIsLoading(false);
        }
    };

    return (
        <div className="carbon-match-page">
            <div className="container">
                <header className="header">
                    <h1><span role="img" aria-label="document">🧾</span> 材料比對工具</h1>
                    <p className="description">
                        上傳材料清單，系統將自動比對資料庫中最相似的標準材料，並提供碳排放數據。
                    </p>
                </header>

                <section className="input-section">
                    <div className="usage-instructions">
                        <h3>📋 使用方式</h3>
                        <ol>
                            <li>點擊「上傳檔案」選擇包含材料名稱的 Excel 檔案</li>
                            <li>系統將自動使用 BM25 算法進行智能匹配</li>
                            <li>跳轉到結果頁面查看匹配結果</li>
                            <li>可在結果頁面進行進階搜尋和手動選擇</li>
                            <li>確認後下載包含碳排放數據的完整結果</li>
                        </ol>
                    </div>

                    <div className="upload-area">
                        <input
                            id="file-upload"
                            type="file"
                            accept=".xlsx,.xls"
                            onChange={handleFile}
                            style={{ display: 'none' }}
                            disabled={isLoading}
                        />
                        <label 
                            htmlFor="file-upload" 
                            className={`btn btn-primary ${isLoading ? 'disabled' : ''}`}
                        >
                            {isLoading ? '處理中...' : (uploaded ? '重新上傳檔案' : '上傳 Excel 檔案')}
                        </label>
                        
                        {uploaded && !isLoading && (
                            <div className="file-status">
                                <span className="file-name">
                                    ✅ 已上傳: {fileName}
                                </span>
                            </div>
                        )}
                    </div>
                </section>

                {isLoading && (
                    <div className="loading-indicator">
                        <div>🔄 正在使用 BM25 算法進行智能匹配...</div>
                        <small>請稍候，系統正在分析您的材料清單</small>
                    </div>
                )}

                {error && (
                    <div className="error-message">
                        ❌ {error}
                    </div>
                )}

                <section className="info-section">
                    <h3>📋 Excel 檔案格式要求</h3>
                    <ul>
                        <li>檔案格式：.xlsx 或 .xls</li>
                        <li>第一列應包含材料名稱（欄位名稱可為：材料名稱、name 或任意名稱）</li>
                        <li>系統會自動讀取第一個工作表的資料</li>
                        <li>建議材料名稱越詳細越好，以提高匹配準確度</li>
                    </ul>
                </section>
            </div>
        </div>
    );
}

export default CarbonMatchPage;
