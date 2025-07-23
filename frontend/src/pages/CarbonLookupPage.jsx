import React, { useState, useEffect, useCallback } from 'react';
import { MATERIAL_API_BASE } from '../api/config';
import './CarbonLookupPage.css';

function CarbonLookupPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [selectedMaterialDetails, setSelectedMaterialDetails] = useState([]);
  const [allMaterials, setAllMaterials] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);

  // 載入所有材料數據
  useEffect(() => {
    const fetchAllMaterials = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`${MATERIAL_API_BASE}/materials/all`);
        const data = await response.json();
        setAllMaterials(data);
        
        // 一開始就顯示所有材料名稱的下拉選單（去重）
        const uniqueNames = [...new Set(data.map(material => material.material_name))];
        setSearchSuggestions(uniqueNames);
        setShowDropdown(true);
        setIsInitialLoad(false);
      } catch (error) {
        console.error('Error fetching materials:', error);
        setIsInitialLoad(false);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllMaterials();
  }, []);

  // 即時搜索建議 - 本地過濾
  const performSearch = useCallback((query) => {
    if (!query.trim()) {
      // 如果搜索為空，顯示所有材料名稱
      const uniqueNames = [...new Set(allMaterials.map(material => material.material_name))];
      setSearchSuggestions(uniqueNames);
      setShowDropdown(true);
      return;
    }

    // 本地過濾搜索
    const filteredResults = allMaterials
      .filter(material =>
        material.material_name.toLowerCase().includes(query.toLowerCase())
      )
      .map(material => material.material_name)
      .filter((name, index, self) => self.indexOf(name) === index); // 去重
    
    setSearchSuggestions(filteredResults);
    setShowDropdown(true);
  }, [allMaterials]);

  // 搜索輸入變化處理
  useEffect(() => {
    if (isInitialLoad) return;
    
    const timeoutId = setTimeout(() => {
      performSearch(searchQuery);
    }, 300); // 300ms防抖

    return () => clearTimeout(timeoutId);
  }, [searchQuery, performSearch, isInitialLoad]);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setSelectedMaterial(null);
    setSelectedMaterialDetails([]);
  };

  const handleSuggestionClick = async (materialName) => {
    setSearchQuery(materialName);
    setSelectedMaterial(materialName);
    setShowDropdown(false);
    
    // 查找所有相同名稱的材料
    const matchingMaterials = allMaterials.filter(
      material => material.material_name === materialName
    );
    
    setSelectedMaterialDetails(matchingMaterials);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchSuggestions.length > 0) {
      handleSuggestionClick(searchSuggestions[0]);
    }
  };

  const handleInputFocus = () => {
    if (searchQuery && searchSuggestions.length > 0) {
      setShowDropdown(true);
    }
  };

  const handleInputBlur = () => {
    // 延遲隱藏下拉選單，讓用戶可以點選建議
    setTimeout(() => {
      setShowDropdown(false);
    }, 200);
  };

  return (
    <div className="carbon-lookup-page">
      <div className="container">
        <header className="header">
          <h1><span role="img" aria-label="search">🔍</span> 碳係數查詢系統</h1>
          <p className="description">
            搜索材料碳排放係數資料庫，查找所有相關的係數記錄。
          </p>
        </header>

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
                placeholder="輸入材料名稱進行搜索..."
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
              <div className="loading-indicator">搜索中...</div>
            ) : selectedMaterial ? (
              <p>找到 <strong>{selectedMaterialDetails.length}</strong> 個 "{selectedMaterial}" 的係數記錄</p>
            ) : searchQuery ? (
              <p>輸入材料名稱並選擇下拉選項</p>
            ) : (
              <p>請輸入材料名稱進行搜索</p>
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
                    <th>材料名稱</th>
                    <th>申報單位</th>
                    <th>碳足跡 (kg CO₂e)</th>
                    <th>數據來源</th>
                    <th>公告年份</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedMaterialDetails.map((material, index) => (
                    <tr key={material.material_id || index}>
                      <td className="material-name">{material.material_name}</td>
                      <td>{material.declaration_unit}</td>
                      <td className="carbon-value">{material.carbon_footprint}</td>
                      <td>{material.data_source}</td>
                      <td className="year-value">{material.announcement_year || '-'}</td>
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