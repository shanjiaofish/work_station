import React, { useState } from 'react';
import './MatchTable.css';

export default function MatchTable({ results, onConfirmSelection }) {
  const [selections, setSelections] = useState({});

  const handleSelect = (originalIndex, material) => {
    const newSelections = {
      ...selections,
      [originalIndex]: material
    };
    setSelections(newSelections);
    onConfirmSelection(originalIndex, material);
  };

  return (
    <div className="match-table-container">
      {results.map((result, index) => (
        <div key={index} className="match-row">
          <div className="original-material">
            <h3>原始材料: {result.original_name}</h3>
          </div>
          
          <div className="matches-container">
            <h4>建議匹配材料:</h4>
            {result.matches && result.matches.length > 0 ? (
              <div className="matches-grid">
                {result.matches.map((match, matchIndex) => (
                  <div 
                    key={matchIndex} 
                    className={`match-card ${selections[result.original_index]?.material_id === match.material_id ? 'selected' : ''}`}
                    onClick={() => handleSelect(result.original_index, match)}
                  >
                    <div className="match-name">{match.material_name}</div>
                    <div className="match-details">
                      <span className="carbon-footprint">碳排放: {match.carbon_footprint} kg CO₂e</span>
                      <span className="unit">單位: {match.declaration_unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-matches">沒有找到匹配的材料</div>
            )}
          </div>

          {selections[result.original_index] && (
            <div className="selected-material">
              <h4>已選擇:</h4>
              <div className="selected-info">
                <span className="selected-name">{selections[result.original_index].material_name}</span>
                <span className="selected-carbon">碳排放: {selections[result.original_index].carbon_footprint} kg CO₂e</span>
                <span className="selected-unit">單位: {selections[result.original_index].declaration_unit}</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
