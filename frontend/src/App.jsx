import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './layout/Layout.jsx'; 
import CarbonMatchPage from './pages/CarbonMatchPage.jsx';
import CarbonLookupPage from './pages/CarbonLookupPage.jsx';
import InvoiceOcrPage from './pages/InvoiceOcrPage.jsx';
import GmapPage from './pages/GmapPage.jsx';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<CarbonMatchPage />} />
        <Route path="carbon-match" element={<CarbonMatchPage />} />
        <Route path="lookup" element={<CarbonLookupPage />} />
        <Route path="ocr" element={<InvoiceOcrPage />} />
        <Route path="gmap" element={<GmapPage />} />
      </Route>
    </Routes>
  );
}
export default App;
