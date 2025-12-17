import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import MatchTable from '../components/MatchTable';
import MaterialUploadPopup from '../components/MaterialUploadPopup';
import DownloadButton from '../components/DownloadButton';
import '../App.css';

function CarbonMatchResultPage() {
    const navigate = useNavigate();
    const { state, actions } = useAppContext();
    const [results, setResults] = useState([]);
    const [sourceData, setSourceData] = useState([]);
    const [selections, setSelections] = useState({});

    useEffect(() => {
        console.log('📖 Reading upload match data from context:', {
            hasUploadMatch: !!state.uploadMatch,
            matchResultsLength: state.uploadMatch?.matchResults?.length || 0,
            sourceDataLength: state.uploadMatch?.sourceData?.length || 0,
            fileName: state.uploadMatch?.fileName,
            selectionsCount: Object.keys(state.uploadMatch?.selections || {}).length
        });

        // Read data from context instead of location.state
        if (state.uploadMatch && state.uploadMatch.matchResults.length > 0) {
            console.log('✅ Setting results from context');
            setResults(state.uploadMatch.matchResults);
            setSourceData(state.uploadMatch.sourceData);
            setSelections(state.uploadMatch.selections);
        } else {
            console.log('❌ No upload match data found in context');
        }
    }, [state.uploadMatch]);

    const handleConfirmSelection = (originalIndex, material) => {
        const updatedSelections = {
            ...selections,
            [originalIndex]: material
        };
        setSelections(updatedSelections);
        // Update selections in context for persistence
        actions.updateUploadMatchSelections(updatedSelections);
    };

    const handleMaterialCreated = (newMaterial) => {
        // 材料創建成功後的處理
        console.log('新材料已創建:', newMaterial);
    };

    const generateDownloadData = () => {
        return results.map((result) => {
            // 使用陣列索引來獲取正確的選擇和原始資料
            const rowIndex = results.indexOf(result);
            const selectedMaterial = selections[rowIndex];
            const originalData = sourceData[rowIndex] || {};

            // 取得第一個建議材料（top suggestion）- 使用後端返回的欄位名稱
            const topSuggestion = result.matches?.[0];
            const suggestionText = topSuggestion
                ? `${topSuggestion.name || topSuggestion.material_name} (${topSuggestion.declaration_unit || topSuggestion.unit}, ${topSuggestion.carbon_footprint || topSuggestion.carbon})`
                : '無建議';

            return {
                '原始名稱': result.query,
                '建議材料選擇': suggestionText,
                '選定名稱': selectedMaterial?.name || topSuggestion?.name || topSuggestion?.material_name || '無匹配',
                '單位': selectedMaterial?.unit || topSuggestion?.declaration_unit || topSuggestion?.unit || '無數據',
                '碳排(kg/CO₂e)': selectedMaterial?.carbon || topSuggestion?.carbon_footprint || topSuggestion?.carbon || '無數據',
                '備註(複合材料)': '',
                '信心度': selectedMaterial?.score || topSuggestion?.score || '無數據',
                '來源': selectedMaterial?.source || topSuggestion?.data_source || topSuggestion?.source || '無數據',
                ...originalData
            };
        });
    };

    if (!results.length) {
        return (
            <div className="container">
                <div className="loading-indicator">
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <h2>📭 沒有上傳的資料</h2>
                        <p>請先上傳 Excel 檔案進行材料匹配</p>
                        <button
                            onClick={() => navigate('/carbon-match')}
                            style={{ marginTop: '20px' }}
                        >
                            前往上傳頁面
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container">
            <h1><span role="img" aria-label="target">🎯</span> 材料匹配結果</h1>
            <p className="description">
                請為每個材料選擇最合適的匹配項目，然後下載完整的碳排放報告。
            </p>

            <div className="results-section">
                <MatchTable
                    results={results}
                    onConfirmSelection={handleConfirmSelection}
                    initialSelections={selections}
                />
            </div>

            <div className="action-bar">
                <button 
                    onClick={() => navigate('/carbon-match')}
                >
                    ← 重新上傳
                </button>
                <DownloadButton data={generateDownloadData()} filename="材料碳排放匹配結果.xlsx" />
            </div>

            <MaterialUploadPopup onCreated={handleMaterialCreated} />
        </div>
    );
}

export default CarbonMatchResultPage;