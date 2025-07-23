import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import './Layout.css';
import '../App.css';

function Layout() {
  return (
    <div className="app-container">
      <nav className="sidebar">
        <h1 className="sidebar-title">工具箱</h1>
        <ul>
          <li><NavLink to="/">上傳檔案配對</NavLink></li>
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