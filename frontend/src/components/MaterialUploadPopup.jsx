import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import './MaterialUploadPopup.css';
import { API_BASE } from '../api/config';

/**
 * Renders a floating "+" button at bottom-right to open a material upload popup form.
 */
export default function MaterialUploadPopup({ onCreated }) {
  const [isOpen, setIsOpen] = useState(false);
  const [form, setForm] = useState({
    material_name: '', carbon_footprint: '', declaration_unit: '',
    data_source: '', life_cycle_scope: '', announcement_year: '',
    verified: '', remarks: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const close = () => {
    setIsOpen(false);
    setError(null);
    setForm({
      material_name: '', carbon_footprint: '', declaration_unit: '',
      data_source: '', life_cycle_scope: '', announcement_year: '',
      verified: '', remarks: '',
    });
  };

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: value,  
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload = {
        ...form,
        carbon_footprint: parseFloat(form.carbon_footprint),
        announcement_year: form.announcement_year ? parseInt(form.announcement_year, 10) : undefined,
      };
      const res = await fetch(`${API_BASE}/materials`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      setLoading(false);
      close();
      onCreated && onCreated(data.data);
    } catch (err) {
      setLoading(false);
      setError(err.message);
    }
  };

  return (
    <>
      {/* Floating + button */}
      <button className="material-upload-trigger" onClick={() => setIsOpen(true)}>
        新增材料
      </button>

      {/* Popup */}
      {isOpen && ReactDOM.createPortal(
        <div className="popup-overlay">
          <div className="popup-content">
            <button className="popup-close" onClick={close}>×</button>
            <h2>新增材料</h2>
            <form onSubmit={handleSubmit}>
              <label>材料名稱 *</label>
              <input name="material_name" required value={form.material_name} onChange={handleChange} />

              <label>碳足跡 *</label>
              <input name="carbon_footprint" type="number" step="0.01" required value={form.carbon_footprint} onChange={handleChange} />

              <label>單位 *</label>
              <input name="declaration_unit" required value={form.declaration_unit} onChange={handleChange} />

              <label>資料來源</label>
              <input name="data_source" value={form.data_source} onChange={handleChange} />

              <label>生命周期範圍</label>
              <input name="life_cycle_scope" value={form.life_cycle_scope} onChange={handleChange} />

              <label>公告年份</label>
              <input name="announcement_year" type="number" value={form.announcement_year} onChange={handleChange} />

              <label>驗證單位</label>
              <input name="verified" value={form.verified} onChange={handleChange} />

              <label>備註</label>
              <textarea name="remarks" value={form.remarks} onChange={handleChange} />

              {error && <p className="error">{error}</p>}
              <div className="actions">
                <button type="button" onClick={close}>取消</button>
                <button type="submit" disabled={loading}>{loading ? '保存中...' : '保存'}</button>
              </div>
            </form>
          </div>
        </div>, document.body
      )}
    </>
  );
}
