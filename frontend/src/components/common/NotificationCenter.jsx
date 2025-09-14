import React from 'react';
import { useNotifications } from '../../hooks/useNotifications';
import './NotificationCenter.css';

function Notification({ notification, onRemove }) {
  const { id, type, title, message, duration } = notification;

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className={`notification notification-${type}`}>
      <div className="notification-icon">
        {getIcon()}
      </div>
      
      <div className="notification-content">
        {title && <h4 className="notification-title">{title}</h4>}
        {message && <p className="notification-message">{message}</p>}
      </div>
      
      <button 
        className="notification-close"
        onClick={() => onRemove(id)}
        aria-label="Close notification"
      >
        ×
      </button>
      
      {duration > 0 && (
        <div 
          className="notification-timer"
          style={{ animationDuration: `${duration}ms` }}
        />
      )}
    </div>
  );
}

function NotificationCenter() {
  const { notifications, removeNotification } = useNotifications();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="notification-center">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          notification={notification}
          onRemove={removeNotification}
        />
      ))}
    </div>
  );
}

export default NotificationCenter;