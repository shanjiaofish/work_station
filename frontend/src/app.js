import { useState, useEffect } from 'react';
import axios from 'axios'; // 引入 axios
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  // 使用 useState 來儲存從後端傳來的訊息
  const [message, setMessage] = useState('正在從後端加載訊息...');

  // useEffect 會在元件第一次被渲染到畫面上時執行一次
  useEffect(() => {
    // 使用 axios 向我們的 Python 後端發送 GET 請求
    axios.get('http://localhost:5000/api/hello')
      .then(response => {
        // 如果成功，就把後端回傳的訊息設定到 message 狀態中
        setMessage(response.data.message);
      })
      .catch(error => {
        // 如果失敗，就顯示錯誤訊息
        console.error('從後端獲取資料時發生錯誤！', error);
        setMessage('無法從後端加載資料，請確認後端伺服器是否已啟動。');
      });
  }, []); // 空陣列 [] 代表這個 effect 只在元件初次渲染時執行一次

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank" rel="noreferrer">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        {/* 在這裡顯示我們從後端獲取的訊息 */}
        <h2>{message}</h2>
      </div>
      <p className="read-the-docs">
        我們的前後端已經成功連線！
      </p>
    </>
  );
}

export default App;