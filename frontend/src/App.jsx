import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Layout from './layout/Layout.jsx'; 
import CarbonMatchPage from './pages/CarbonMatchPage.jsx';
import CarbonMatchResultPage from './pages/CarbonMatchResultPage.jsx';
import CarbonLookupPage from './pages/CarbonLookupPage.jsx';
import InvoiceOcrPage from './pages/InvoiceOcrPage.jsx';
import GmapPage from './pages/GmapPage.jsx';
import NotificationCenter from './components/common/NotificationCenter';
import './App.css';

function App() {
  return (
    <AppProvider>
      <div className="app">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<CarbonMatchPage />} />
            <Route path="carbon-match" element={<CarbonMatchPage />} />
            <Route path="carbon-match-result" element={<CarbonMatchResultPage />} />
            <Route path="lookup" element={<CarbonLookupPage />} />
            <Route path="ocr" element={<InvoiceOcrPage />} />
            <Route path="gmap" element={<GmapPage />} />
          </Route>
        </Routes>
        <NotificationCenter />
      </div>
    </AppProvider>
  );
}
export default App;
