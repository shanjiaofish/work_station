import { useCallback, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';

export function useNotifications() {
  const { state, actions } = useAppContext();

  const addNotification = useCallback((notification) => {
    const defaultDuration = {
      'success': 4000,
      'error': 6000,
      'warning': 5000,
      'info': 3000
    };

    const notificationWithDefaults = {
      type: 'info',
      title: '',
      message: '',
      duration: defaultDuration[notification.type] || 4000,
      ...notification
    };

    actions.addNotification(notificationWithDefaults);

    // Auto-remove notification after duration
    if (notificationWithDefaults.duration > 0) {
      setTimeout(() => {
        actions.removeNotification(notificationWithDefaults.id);
      }, notificationWithDefaults.duration);
    }

    return notificationWithDefaults.id;
  }, [actions]);

  const removeNotification = useCallback((id) => {
    actions.removeNotification(id);
  }, [actions]);

  const clearAllNotifications = useCallback(() => {
    state.ui.notifications.forEach(notification => {
      actions.removeNotification(notification.id);
    });
  }, [state.ui.notifications, actions]);

  // Auto-remove old notifications
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      state.ui.notifications.forEach(notification => {
        if (notification.createdAt && (now - notification.createdAt) > (notification.duration || 4000)) {
          actions.removeNotification(notification.id);
        }
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [state.ui.notifications, actions]);

  return {
    notifications: state.ui.notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    
    // Convenience methods
    success: (title, message, options = {}) => addNotification({ 
      type: 'success', title, message, ...options 
    }),
    error: (title, message, options = {}) => addNotification({ 
      type: 'error', title, message, ...options 
    }),
    warning: (title, message, options = {}) => addNotification({ 
      type: 'warning', title, message, ...options 
    }),
    info: (title, message, options = {}) => addNotification({ 
      type: 'info', title, message, ...options 
    })
  };
}