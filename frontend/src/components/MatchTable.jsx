import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import axios from 'axios';
import { API_BASE } from '../api/config';
import './MatchTable.css';

export default function MatchTable({
  results: matchResults,
  onConfirmSelection
}) {
  const [advancedRows, setAdvancedRows] = useState([]);
  const [selections, setSelections] = useState([]);
  const [allMaterialsForSelect, setAllMaterialsForSelect] = useState([]);

  // 初始化選擇狀態 - 使用默認推薦的材料
  useEffect(() => {
    if (matchResults) {
      const initialSelections = matchResults.map((result, index) => {
        if (result && Array.isArray(result.matches) && result.matches.length > 0) {
          const defaultIndex = (typeof result.default === 'number' && result.default >= 0 && result.default < result.matches.length)
                               ? result.default
                               : 0;
          return result.matches[defaultIndex] || result.matches[0] || null;
        }
        // 如果沒有匹配結果，創建一個空的佔位符
        return {
          name: result?.query || '',
          unit: '', 
          carbon: '', 
          source: 'no_initial_match',
          id: `placeholder-${index}-${Date.now()}`
        };
      });
      setSelections(initialSelections);
    }
  }, [matchResults]);

  // 獲取完整材料數據庫用於進階搜尋
  useEffect(() => {
    axios.get(`${API_BASE}/api/materials/all`)
      .then(res => {
        // Handle new response format
        const materials = res.data.success ? res.data.data : res.data;
        const formattedMaterials = materials.map(m => ({
          value: {
            id: m.material_id, 
            name: m.material_name, 
            unit: m.declaration_unit, 
            carbon: m.carbon_footprint,
            source: m.data_source
          },
          label: `${m.material_name} (${m.declaration_unit}, ${m.carbon_footprint})`
        }));
        setAllMaterialsForSelect(formattedMaterials);
      })
      .catch(err => {
        console.error('Error fetching materials:', err);
        // 如果API失敗，從匹配結果中提取材料作為備用
        if (matchResults) {
          const allAvailableMaterials = [];
          matchResults.forEach(result => {
            if (result.matches && result.matches.length > 0) {
              allAvailableMaterials.push(...result.matches);
            }
          });
          const uniqueMaterials = allAvailableMaterials
            .filter((material, index, self) => 
              index === self.findIndex(m => 
                (m.id || m.material_id) === (material.id || material.material_id)
              )
            )
            .map(m => ({
              value: {
                id: m.id || m.material_id,
                name: m.name || m.material_name,
                unit: m.unit || m.declaration_unit,
                carbon: m.carbon || m.carbon_footprint,
                source: m.source || m.data_source
              },
              label: `${m.name || m.material_name} (${m.unit || m.declaration_unit}, ${m.carbon || m.carbon_footprint})`
            }));
          setAllMaterialsForSelect(uniqueMaterials);
        }
      }); 
  }, [matchResults]);

  const toggleMode = (rowIndex) => {
    setAdvancedRows(prev =>
      prev.includes(rowIndex)
        ? prev.filter(idx => idx !== rowIndex)
        : [...prev, rowIndex]
    );
  };

  const handleSelect = (rowIndex, option) => {
    const updated = [...selections];
    updated[rowIndex] = option ? option.value : selections[rowIndex]; // 保持當前選擇如果沒有新選擇
    setSelections(updated);
    if (onConfirmSelection) {
      onConfirmSelection(rowIndex, updated[rowIndex]);
    }
  };

  const handleMenuOpen = (rowIndex) => {
    // 當點擊搜尋框時清空當前選擇，提供乾淨的輸入體驗
    const updated = [...selections];
    updated[rowIndex] = {
      name: '',
      unit: '',
      carbon: '',
      source: 'cleared_for_search',
      id: `cleared-${rowIndex}-${Date.now()}`
    };
    setSelections(updated);
    if (onConfirmSelection) {
      onConfirmSelection(rowIndex, updated[rowIndex]);
    }
  };

  if (!matchResults || matchResults.length === 0) {
    return <div>沒有匹配結果</div>;
  }

  return (
    <table className="match-table">
      <thead>
        <tr>
          <th className="col-original">原始名稱</th>
          <th className="col-suggestions">建議材料選擇</th>
          <th className="col-selected">選定名稱</th>
          <th className="col-unit">單位</th>
          <th className="col-carbon">碳排(kg/CO₂e)</th>
        </tr>
      </thead>
      <tbody>
        {matchResults.map((row, i) => {
          const isAdvanced = advancedRows.includes(i);
          
          // 原始顯示前 5 項BM25匹配結果
          const originalOptions = (row.matches || [])
            .slice(0, 5)
            .map(m => ({ 
              value: {
                id: m.id || m.material_id,
                name: m.name || m.material_name,
                unit: m.unit || m.declaration_unit,
                carbon: m.carbon || m.carbon_footprint,
                source: m.source || m.data_source || 'BM25匹配',
                score: m.score
              }, 
              label: `${m.name || m.material_name} (${m.unit || m.declaration_unit || 'kg'}, ${m.carbon || m.carbon_footprint || 0})` 
            }));
          
          // 進階搜尋：使用完整材料數據庫
          const currentOptions = isAdvanced ? allMaterialsForSelect : originalOptions;

          // 找到當前選擇的值
          const current = selections[i];
          let selectedValue = null;
          
          if (current && current.source !== 'cleared_for_search' && current.name) {
            selectedValue = currentOptions.find(opt => 
              (opt.value.id === current?.id) || 
              (opt.value.name === current?.name)
            );
          }
          
          const placeholder = isAdvanced ? "🔍 搜尋完整材料數據庫..." : "選擇BM25推薦材料...";
        
          return (
            <tr key={row.query || i}>
              <td>{row.query}</td>
              <td>
                <div className="match-cell">
                  <Select
                    key={`select-${i}-${isAdvanced}`}
                    className="match-select"
                    classNamePrefix="match-select"
                    options={currentOptions}
                    value={selectedValue || null}
                    onChange={opt => handleSelect(i, opt)}
                    onMenuOpen={() => handleMenuOpen(i)}
                    isSearchable={true}
                    placeholder={placeholder}
                    noOptionsMessage={() => '無匹配選項'}
                    isClearable
                    filterOption={(option, searchText) => {
                      if (!searchText) return true;
                      const label = option.label.toLowerCase();
                      const search = searchText.toLowerCase();
                      return label.includes(search);
                    }}
                    menuPlacement="auto"
                    maxMenuHeight={200}
                    styles={{
                      control: (provided) => ({
                        ...provided,
                        minHeight: '38px'
                      })
                    }}
                  />
                  <button
                    className={`toggle-btn-${isAdvanced ? 'advanced' : 'original'}`}
                    onClick={() => toggleMode(i)}
                    title={isAdvanced ? '切換到BM25建議材料' : '切換到完整材料數據庫搜尋'}
                  >
                    {isAdvanced ? 'BM25' : '完整庫'}
                  </button>
                </div>
              </td>
              <td>{current?.name || current?.material_name || ''}</td>
              <td>{current?.unit || current?.declaration_unit || ''}</td>
              <td>{current?.carbon || current?.carbon_footprint || ''}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
