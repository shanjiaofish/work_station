import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useMaterials } from '../hooks/useMaterials';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import './CarbonLookupPage.css';
import { API_BASE } from '../api/config';
import { normalizeText } from '../utils/textNormalization';

function CarbonLookupPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [selectedMaterialDetails, setSelectedMaterialDetails] = useState([]);
  const [allMaterials, setAllMaterials] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  
  // Excel import states
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [showImportPanel, setShowImportPanel] = useState(false);
  const fileInputRef = useRef(null);
  
  // Excel preview states
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewStats, setPreviewStats] = useState(null);
  
  const { searchMaterials, isLoading } = useMaterials();

  // 載入所有材料數據
  useEffect(() => {
    const fetchAllMaterials = async () => {
      try {
        console.log('🔄 Fetching all materials from database...');
        setIsInitialLoad(true); // Show loading state
        
        const startTime = Date.now();
        const response = await fetch(`${API_BASE}/api/materials/all`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        const loadTime = Date.now() - startTime;
        
        // Handle new response format
        const materials = result.success ? result.data : result;
        console.log(`✅ Fetched ${materials.length} materials in ${loadTime}ms`);
        
        setAllMaterials(materials);
        
        // 準備搜索建議，但不立即顯示下拉選單
        const uniqueNames = [...new Set(materials.map(material => material.material_name))];
        setSearchSuggestions(uniqueNames);
        setShowDropdown(false); // 初始不顯示下拉選單
        setIsInitialLoad(false);
      } catch (error) {
        console.error('Error loading materials:', error);
        // Fallback to empty state if database is not available
        setAllMaterials([]);
        setSearchSuggestions([]);
        setIsInitialLoad(false);
      }
    };

    fetchAllMaterials();
  }, []); // Remove notifyError from dependencies to prevent infinite loop

  // 即時搜索建議 - 本地過濾
  const performSearch = useCallback((query) => {
    if (!Array.isArray(allMaterials)) {
      setSearchSuggestions([]);
      return;
    }
    
    if (!query.trim()) {
      // 如果搜索為空，隱藏下拉選單
      setSearchSuggestions([]);
      setShowDropdown(false);
      return;
    }

    // 本地過濾搜索 - 使用正規化比對
    const normalizedQuery = normalizeText(query);
    const filteredResults = allMaterials
      .filter(material =>
        material.material_name && normalizeText(material.material_name).includes(normalizedQuery)
      )
      .map(material => material.material_name)
      .filter((name, index, self) => self.indexOf(name) === index); // 去重
    
    setSearchSuggestions(filteredResults);
    // 只有當有搜索結果時才顯示下拉選單
    setShowDropdown(filteredResults.length > 0);
  }, [allMaterials]);

  // 搜索輸入變化處理
  useEffect(() => {
    if (isInitialLoad || !Array.isArray(allMaterials)) return;
    
    const timeoutId = setTimeout(() => {
      if (!searchQuery.trim()) {
        // 如果搜索為空，準備顯示所有材料（但不立即顯示dropdown，等focus時顯示）
        const uniqueNames = [...new Set(allMaterials.map(material => material.material_name))];
        setSearchSuggestions(uniqueNames);
        setShowDropdown(false); // 清空輸入時不自動顯示，等用戶點擊時顯示
        return;
      }

      // 本地過濾搜索 - 使用正規化比對
      const normalizedQuery = normalizeText(searchQuery);
      const filteredResults = allMaterials
        .filter(material =>
          material.material_name && normalizeText(material.material_name).includes(normalizedQuery)
        )
        .map(material => material.material_name)
        .filter((name, index, self) => self.indexOf(name) === index); // 去重
      
      setSearchSuggestions(filteredResults);
      // 只有當有搜索結果時才顯示下拉選單
      setShowDropdown(filteredResults.length > 0);
    }, 300); // 300ms防抖

    return () => clearTimeout(timeoutId);
  }, [searchQuery, allMaterials, isInitialLoad]);

  const handleSearchChange = (e) => {
    const newValue = e.target.value;
    setSearchQuery(newValue);
    setSelectedMaterial(null);
    setSelectedMaterialDetails([]);
    
    // 如果用戶清空了輸入，確保下次focus時能顯示所有材料
    if (!newValue.trim() && Array.isArray(allMaterials)) {
      const uniqueNames = [...new Set(allMaterials.map(material => material.material_name))];
      setSearchSuggestions(uniqueNames);
    }
  };

  const handleSuggestionClick = async (materialName) => {
    setSearchQuery(materialName);
    setSelectedMaterial(materialName);
    setShowDropdown(false);
    setSearchSuggestions([]); // 清空建議列表
    
    // 查找所有相同名稱的材料
    if (Array.isArray(allMaterials)) {
      const matchingMaterials = allMaterials.filter(
        material => material.material_name === materialName
      );
      
      setSelectedMaterialDetails(matchingMaterials);
    } else {
      setSelectedMaterialDetails([]);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchSuggestions.length > 0) {
      handleSuggestionClick(searchSuggestions[0]);
    }
  };

  const handleInputFocus = () => {
    // 當輸入框獲得焦點時，總是顯示可用的材料選項
    if (!Array.isArray(allMaterials)) return;
    
    if (!searchQuery || !searchQuery.trim()) {
      // 如果輸入為空，顯示所有材料
      const uniqueNames = [...new Set(allMaterials.map(material => material.material_name))];
      setSearchSuggestions(uniqueNames);
      setShowDropdown(uniqueNames.length > 0);
    } else {
      // 如果有輸入內容，顯示過濾後的結果
      setShowDropdown(searchSuggestions.length > 0);
    }
  };

  const handleInputBlur = () => {
    // 延遲隱藏下拉選單，讓用戶可以點選建議
    setTimeout(() => {
      setShowDropdown(false);
    }, 150);
  };

  // Excel import functions
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleExcelPreview(file);
    }
  };

  const handleExcelPreview = async (file) => {
    setIsPreviewing(true);
    setImportResult(null);
    setPreviewData(null);
    setShowPreview(false);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      console.log('🔄 Previewing Excel file...');
      const response = await fetch(`${API_BASE}/api/materials/preview-excel`, {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Preview failed');
      }
      
      console.log('✅ Preview completed:', result);
      setPreviewData(result.preview_data);
      setPreviewStats({
        total_rows: result.total_rows,
        valid_rows: result.valid_rows,
        invalid_rows: result.invalid_rows,
        validation_errors: result.validation_errors
      });
      setShowPreview(true);
      
    } catch (error) {
      console.error('Preview error:', error);
      setImportResult({
        error: true,
        message: error.message
      });
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleExcelImport = async () => {
    if (!previewData || !previewStats) {
      alert('請先選擇並預覽 Excel 檔案');
      return;
    }
    
    if (previewStats.valid_rows === 0) {
      alert('沒有有效的資料可以上傳');
      return;
    }
    
    setIsImporting(true);
    setImportResult(null);
    
    try {
      console.log('🔄 Uploading materials to database...');
      const response = await fetch(`${API_BASE}/api/materials/import-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          materials: previewData
        })
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Import failed');
      }
      
      console.log('✅ Import completed:', result);
      setImportResult(result);
      
      // Clear preview data after successful import
      setPreviewData(null);
      setShowPreview(false);
      setPreviewStats(null);
      
      // Refresh materials list after successful import
      if (result.imported_count > 0) {
        console.log('🔄 Refreshing materials list...');
        const materialsResponse = await fetch(`${API_BASE}/api/materials/all`);
        if (materialsResponse.ok) {
          const materialsResult = await materialsResponse.json();
          // Handle new response format
          const materials = materialsResult.success ? materialsResult.data : materialsResult;
          setAllMaterials(materials);
          
          // Update search suggestions
          const uniqueNames = [...new Set(materials.map(material => material.material_name))];
          setSearchSuggestions(uniqueNames);
        }
      }
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Import error:', error);
      setImportResult({
        error: true,
        message: error.message
      });
    } finally {
      setIsImporting(false);
    }
  };

  const toggleImportPanel = () => {
    setShowImportPanel(!showImportPanel);
    setImportResult(null);
  };

  const handleDownloadTemplate = async () => {
    try {
      console.log('🔄 Downloading Excel template...');
      const response = await fetch(`${API_BASE}/api/materials/template`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '材料匯入範本.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Template downloaded successfully');
    } catch (error) {
      console.error('Template download error:', error);
      alert('下載範本失敗，請稍後再試');
    }
  };

  return (
    <div className="carbon-lookup-page">
      <div className="container">
        <header className="header">
          <h1><span role="img" aria-label="search">🔍</span> 碳係數查詢系統</h1>
          <p className="description">
            搜索材料碳排放係數資料庫，查找所有相關的係數記錄。
          </p>
          
          {/* Excel Import Toggle Button */}
          <div className="import-controls">
            <button 
              onClick={toggleImportPanel}
              className="btn btn-secondary"
              style={{
                backgroundColor: '#6c757d',
                color: 'white', 
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: 'pointer',
                marginTop: '10px'
              }}
            >
              📊 {showImportPanel ? '隱藏' : '新增'}  數據至資料庫
            </button>
            <span style={{ marginLeft: '10px', color: '#666' }}>
              目前資料庫共 {allMaterials.length} 筆材料
            </span>
          </div>
        </header>

        {/* Excel Import Panel */}
        {showImportPanel && (
          <section className="import-section" style={{
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <h3>📊 Excel 資料匯入</h3>
            <p style={{ color: '#666', marginBottom: '15px' }}>
              支援 .xlsx 和 .xls 格式。Excel 檔案需包含以下必要欄位：
              <strong> material_name, carbon_footprint, declaration_unit</strong>
            </p>
            <p style={{ color: '#666', fontSize: '0.9em', marginBottom: '15px' }}>
              可選欄位：data_source, announcement_year, life_cycle_scope, verified, remarks
            </p>
            
            <div style={{ marginBottom: '15px' }}>
              <button 
                onClick={handleDownloadTemplate}
                className="btn btn-outline-primary"
                style={{
                  backgroundColor: 'transparent',
                  color: '#007bff', 
                  border: '1px solid #007bff',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                📁 下載 Excel 範本
              </button>
              <span style={{ fontSize: '0.8em', color: '#666' }}>
                包含所有欄位說明和範例資料
              </span>
            </div>
            
            <div className="file-input-container">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                disabled={isPreviewing || isImporting}
                style={{ marginBottom: '10px' }}
              />
              
              {isPreviewing && (
                <div style={{ margin: '10px 0' }}>
                  <LoadingSpinner size="small" message="正在預覽檔案..." />
                </div>
              )}
              
              {isImporting && (
                <div style={{ margin: '10px 0' }}>
                  <LoadingSpinner size="small" message="正在上傳到資料庫..." />
                </div>
              )}
              
              {importResult && (
                <div style={{
                  padding: '10px',
                  borderRadius: '4px',
                  marginTop: '10px',
                  backgroundColor: importResult.error ? '#f8d7da' : '#d4edda',
                  color: importResult.error ? '#721c24' : '#155724',
                  border: `1px solid ${importResult.error ? '#f5c6cb' : '#c3e6cb'}`
                }}>
                  {importResult.error ? (
                    <div>
                      <strong>❌ 匯入失敗</strong>
                      <p>{importResult.message}</p>
                    </div>
                  ) : (
                    <div>
                      <strong>✅ {importResult.message}</strong>
                      {importResult.errors && importResult.errors.length > 0 && (
                        <details style={{ marginTop: '10px' }}>
                          <summary>查看錯誤詳情 ({importResult.errors.length})</summary>
                          <ul style={{ marginTop: '5px' }}>
                            {importResult.errors.map((error, index) => (
                              <li key={index} style={{ fontSize: '0.9em' }}>{error}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        )}

        {/* Excel Preview Section */}
        {showPreview && previewData && previewStats && (
          <section className="preview-section" style={{
            backgroundColor: '#fff',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <h3>📋 Excel 資料預覽</h3>
            
            {/* Preview Statistics */}
            <div style={{
              backgroundColor: '#f8f9fa',
              padding: '15px',
              borderRadius: '6px',
              marginBottom: '15px',
              display: 'flex',
              gap: '20px',
              flexWrap: 'wrap'
            }}>
              <span style={{ color: '#28a745', fontWeight: 'bold' }}>
                ✅ 有效資料: {previewStats.valid_rows} 筆
              </span>
              <span style={{ color: '#dc3545', fontWeight: 'bold' }}>
                ❌ 錯誤資料: {previewStats.invalid_rows} 筆
              </span>
              <span style={{ color: '#6c757d' }}>
                📊 總計: {previewStats.total_rows} 筆
              </span>
            </div>

            {/* Upload Button */}
            {previewStats.valid_rows > 0 && (
              <div style={{ marginBottom: '15px' }}>
                <button
                  onClick={handleExcelImport}
                  disabled={isImporting}
                  style={{
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '4px',
                    cursor: isImporting ? 'not-allowed' : 'pointer',
                    marginRight: '10px',
                    opacity: isImporting ? 0.6 : 1
                  }}
                >
                  {isImporting ? '⏳ 上傳中...' : `✅ 確認上傳 ${previewStats.valid_rows} 筆有效資料`}
                </button>
                <button
                  onClick={() => {
                    setShowPreview(false);
                    setPreviewData(null);
                    setPreviewStats(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  disabled={isImporting}
                  style={{
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '4px',
                    cursor: isImporting ? 'not-allowed' : 'pointer',
                    opacity: isImporting ? 0.6 : 1
                  }}
                >
                  ❌ 取消
                </button>
              </div>
            )}

            {/* Validation Errors Summary */}
            {previewStats.validation_errors && previewStats.validation_errors.length > 0 && (
              <details style={{ marginBottom: '15px' }}>
                <summary style={{ color: '#dc3545', cursor: 'pointer', fontWeight: 'bold' }}>
                  ⚠️ 發現 {previewStats.validation_errors.length} 個驗證錯誤
                </summary>
                <ul style={{ marginTop: '10px', maxHeight: '200px', overflowY: 'auto' }}>
                  {previewStats.validation_errors.map((error, index) => (
                    <li key={index} style={{ color: '#dc3545', fontSize: '0.9em', marginBottom: '5px' }}>
                      {error}
                    </li>
                  ))}
                </ul>
              </details>
            )}

            {/* Preview Table */}
            <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.9em'
              }}>
                <thead style={{ backgroundColor: '#f8f9fa', position: 'sticky', top: 0 }}>
                  <tr>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>行號</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>狀態</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>材料名稱</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>碳足跡</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>申報單位</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>數據來源</th>
                    <th style={{ border: '1px solid #dee2e6', padding: '8px', textAlign: 'left' }}>公告年份</th>
                  </tr>
                </thead>
                <tbody>
                  {previewData.map((row, index) => (
                    <tr key={index} style={{
                      backgroundColor: row.is_valid ? 'transparent' : '#fff5f5'
                    }}>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.row_index}</td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>
                        {row.is_valid ? (
                          <span style={{ color: '#28a745' }}>✅</span>
                        ) : (
                          <span style={{ color: '#dc3545' }} title={row.errors.join(', ')}>❌</span>
                        )}
                      </td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.material_name}</td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.carbon_footprint}</td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.declaration_unit}</td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.data_source || '-'}</td>
                      <td style={{ border: '1px solid #dee2e6', padding: '8px' }}>{row.announcement_year || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Loading State for Initial Data Fetch */}
        {isInitialLoad && (
          <section className="loading-section" style={{
            textAlign: 'center',
            padding: '40px 20px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            margin: '20px 0'
          }}>
            <LoadingSpinner size="large" message="正在載入完整材料資料庫..." />
            <p style={{ color: '#666', marginTop: '15px', fontSize: '0.9em' }}>
              首次載入可能需要幾秒鐘，我們正在取得所有材料資料以提供完整的搜索功能。
            </p>
          </section>
        )}

        <section className="input-section">
          <div className="form-group">
            <label htmlFor="material-search">材料名稱搜索</label>
            <div className="search-input-container">
              <input
                id="material-search"
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder="點擊查看所有材料或輸入搜索..."
                className="form-control"
                autoFocus
              />
              
              {/* 下拉建議選單 */}
              {showDropdown && searchSuggestions.length > 0 && (
                <div className="dropdown-suggestions">
                  {searchSuggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className="suggestion-item"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      🔍 {suggestion}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 搜索統計信息 */}
          <div className="search-stats">
            {isLoading ? (
              <LoadingSpinner size="small" message="搜索中..." />
            ) : selectedMaterial ? (
              <p>找到 <strong>{selectedMaterialDetails.length}</strong> 個 "{selectedMaterial}" 的係數記錄</p>
            ) : searchQuery && searchQuery.trim() ? (
              <p>請從下拉選單中選擇材料</p>
            ) : (
              <p>點擊搜索框查看所有可用材料</p>
            )}
          </div>
        </section>

        {/* 選中材料的詳細信息 */}
        {selectedMaterial && selectedMaterialDetails.length > 0 && (
          <section className="results-section">
            <h2>"{selectedMaterial}" 的所有係數記錄</h2>
            
            <div className="table-container">
              <table className="materials-table">
                <thead>
                  <tr>
                    <th>碳係數名稱</th>
                    <th>數值</th>
                    <th>宣告單位</th>
                    <th>公告單位</th>
                    <th>公告年份</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedMaterialDetails.map((material, index) => (
                    <tr key={material.material_id || index}>
                      <td>{material.material_name}</td>
                      <td>{material.carbon_footprint}</td>
                      <td>{material.declaration_unit}</td>
                      <td>{material.data_source || '-'}</td>
                      <td>{material.announcement_year || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* 無結果狀態 */}
        {selectedMaterial && selectedMaterialDetails.length === 0 && (
          <div className="error-message">
            沒有找到 "{selectedMaterial}" 的相關係數，請嘗試使用不同的關鍵字搜索。
          </div>
        )}
      </div>
    </div>
  );
}

export default CarbonLookupPage;