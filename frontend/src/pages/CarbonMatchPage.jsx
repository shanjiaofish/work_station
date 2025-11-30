import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { useNavigate } from 'react-router-dom';
import { useMaterials } from '../hooks/useMaterials';
import { useNotifications } from '../hooks/useNotifications';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import { API_BASE } from '../api/config';
import '../App.css';

function CarbonMatchPage() {
    const [uploaded, setUploaded] = useState(false);
    const [fileName, setFileName] = useState('');
    const navigate = useNavigate();
    const { batchMatchMaterials, isLoading, error, clearError } = useMaterials();
    const { success, error: notifyError } = useNotifications();

    // 處理檔案上傳
    const handleFile = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
            notifyError('格式錯誤', '請選擇 Excel 檔案 (.xlsx 或 .xls)');
            return;
        }

        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            notifyError('檔案過大', '檔案大小不能超過 10MB');
            return;
        }

        setFileName(file.name);
        setUploaded(true);
        clearError();

        try {
            const reader = new FileReader();
            reader.onload = async (evt) => {
                try {
                    const wb = XLSX.read(evt.target.result, { type: 'binary' });
                    
                    if (!wb.SheetNames || wb.SheetNames.length === 0) {
                        throw new Error('Excel 檔案中沒有找到工作表');
                    }

                    const sheet = wb.Sheets[wb.SheetNames[0]];
                    const data = XLSX.utils.sheet_to_json(sheet);

                    if (!data || data.length === 0) {
                        throw new Error('Excel 檔案中沒有找到數據');
                    }
                    
                    // 提取材料名稱進行批量匹配
                    const queries = data
                        .map(row => row['材料名稱'] || row['name'] || row[Object.keys(row)[0]])
                        .filter(query => query && typeof query === 'string' && query.trim() !== '')
                        .map(query => query.trim());

                    if (queries.length === 0) {
                        throw new Error('沒有找到有效的材料名稱。請確認第一列包含材料名稱。');
                    }

                    success('檔案讀取成功', `找到 ${queries.length} 個材料項目，開始進行匹配...`);
                    
                    // 批量匹配材料
                    const matchResults = await batchMatchMaterials(queries);
                    
                    // 跳轉到結果頁面
                    navigate('/carbon-match-result', {
                        state: {
                            sourceData: data,
                            matchResults: matchResults,
                            fileName: file.name
                        }
                    });
                    
                } catch (parseError) {
                    console.error('Excel 檔案解析錯誤:', parseError);
                    notifyError('檔案解析失敗', parseError.message || '請確認這是一個有效的 Excel 檔案');
                    setUploaded(false);
                }
            };
            
            reader.onerror = () => {
                console.error('檔案讀取錯誤');
                notifyError('檔案讀取失敗', '請重新選擇檔案');
                setUploaded(false);
            };
            
            reader.readAsArrayBuffer(file);
            
        } catch (err) {
            console.error('處理檔案時發生錯誤:', err);
            notifyError('檔案處理失敗', err.message || '請檢查檔案格式是否正確');
            setUploaded(false);
        }
    };

    // 處理範本下載
    const handleDownloadTemplate = async () => {
        try {
            console.log('🔄 Downloading match template...');
            const response = await fetch(`${API_BASE}/api/materials/match-template`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = '材料配對匯入範本.xlsx';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            console.log('✅ Match template downloaded successfully');
            success('下載成功', '已下載材料配對範本');
        } catch (error) {
            console.error('Template download error:', error);
            notifyError('下載失敗', '下載範本失敗，請稍後再試');
        }
    };

    return (
        <div className="carbon-match-page">
            <div className="container">
                <header className="main-header">
                    <h1><span role="img" aria-label="document">🧾</span> 材料比對工具</h1>
                    <p className="description">
                        上傳您的材料清單，系統將自動比對資料庫中最相似的標準材料，並提供詳細的碳排放數據分析。
                    </p>
                </header>

                <section className="usage-instructions">
                    <h3>使用說明</h3>
                    <ol>
                        <li>選擇包含材料名稱的 Excel 檔案</li>
                        <li>系統會自動使用 BM25 算法進行材料匹配</li>
                        <li>檢視匹配結果並選擇最合適的材料</li>
                        <li>下載完整的碳排放數據報告</li>
                    </ol>
                </section>

                <section className="template-section" style={{ textAlign: 'center', margin: '20px 0' }}>
                    <button
                        onClick={handleDownloadTemplate}
                        className="btn btn-outline-primary"
                        style={{
                            backgroundColor: 'transparent',
                            color: '#007bff',
                            border: '1px solid #007bff',
                            padding: '10px 20px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '1em'
                        }}
                    >
                        📁 下載 Excel 範本
                    </button>
                    <div style={{ fontSize: '0.85em', color: '#666', marginTop: '8px' }}>
                        包含材料名稱欄位及範例資料
                    </div>
                </section>

                <section className="input-section">
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
                            {isLoading ? '處理中...' : (uploaded ? '重新上傳檔案' : '選擇 Excel 檔案')}
                        </label>

                        {uploaded && !isLoading && (
                            <div className="file-status">
                                <span className="file-name">已選擇: {fileName}</span>
                            </div>
                        )}
                    </div>
                </section>

                {isLoading && (
                    <LoadingSpinner 
                        size="large"
                        message="正在進行材料匹配分析，請稍候..."
                    />
                )}

                {error && (
                    <ErrorMessage
                        title="處理失敗"
                        message={error}
                        onRetry={() => {
                            clearError();
                            setUploaded(false);
                            setFileName('');
                        }}
                        onDismiss={clearError}
                    />
                )}

                <section className="info-section">
                    <h3>檔案格式要求</h3>
                    <ul>
                        <li>支援 .xlsx 或 .xls 格式</li>
                        <li>第一列應包含材料名稱</li>
                        <li>材料名稱越詳細，匹配準確度越高</li>
                    </ul>
                </section>
            </div>
        </div>
    );
}

export default CarbonMatchPage;
