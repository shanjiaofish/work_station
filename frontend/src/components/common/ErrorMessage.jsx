import React from 'react';
import './ErrorMessage.css';

function ErrorMessage({ 
  title = 'Error',
  message,
  onRetry,
  onDismiss,
  type = 'error',
  className = '',
  showIcon = true
}) {
  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      case 'success':
        return '✅';
      default:
        return '❌';
    }
  };

  return (
    <div className={`error-message ${type} ${className}`}>
      <div className="error-content">
        {showIcon && (
          <span className="error-icon" role="img" aria-label={type}>
            {getIcon()}
          </span>
        )}
        <div className="error-text">
          <h4 className="error-title">{title}</h4>
          {message && <p className="error-description">{message}</p>}
        </div>
      </div>
      
      {(onRetry || onDismiss) && (
        <div className="error-actions">
          {onRetry && (
            <button 
              className="btn btn-retry"
              onClick={onRetry}
              type="button"
            >
              重試
            </button>
          )}
          {onDismiss && (
            <button 
              className="btn btn-dismiss"
              onClick={onDismiss}
              type="button"
              aria-label="Dismiss"
            >
              ×
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default ErrorMessage;