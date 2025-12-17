import React from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import './Layout.css';
import '../App.css';

function Layout() {
  const { state } = useAppContext();
  const navigate = useNavigate();
  const location = useLocation();

  // Check if there's upload match data in context
  const hasUploadData = state.uploadMatch &&
                        state.uploadMatch.matchResults &&
                        state.uploadMatch.matchResults.length > 0;

  // Handle navigation for upload/match link
  const handleUploadLinkClick = (e) => {
    e.preventDefault();
    // If data exists, go to results page; otherwise go to upload page
    if (hasUploadData) {
      navigate('/carbon-match-result');
    } else {
      navigate('/carbon-match');
    }
  };

  // Determine if the upload/match link is active
  const isUploadMatchActive = location.pathname === '/' ||
                               location.pathname === '/carbon-match' ||
                               location.pathname === '/carbon-match-result';

  return (
    <div className="app-container">
      <nav className="sidebar">
        <h1 className="sidebar-title">工具箱</h1>
        <ul>
          <li>
            <a
              href="#"
              onClick={handleUploadLinkClick}
              className={isUploadMatchActive ? 'active' : ''}
            >
              上傳檔案配對
            </a>
          </li>
          <li><NavLink to="/lookup">查找碳係數</NavLink></li>
          <li><NavLink to="/ocr">發票 OCR</NavLink></li>
          <li><NavLink to="/gmap">地圖截圖</NavLink></li>
        </ul>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
export default Layout;