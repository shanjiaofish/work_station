import React from 'react';
import './LoadingSpinner.css';

function LoadingSpinner({ 
  size = 'medium', 
  message = 'Loading...', 
  showMessage = true,
  className = '',
  color = 'primary'
}) {
  const sizeClass = `spinner-${size}`;
  const colorClass = `spinner-${color}`;

  return (
    <div className={`loading-spinner ${className}`}>
      <div className={`spinner ${sizeClass} ${colorClass}`}></div>
      {showMessage && message && (
        <p className="loading-message">{message}</p>
      )}
    </div>
  );
}

export default LoadingSpinner;