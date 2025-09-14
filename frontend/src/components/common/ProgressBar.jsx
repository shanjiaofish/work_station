import React from 'react';
import './ProgressBar.css';

function ProgressBar({
  progress = 0,
  message = '',
  showPercentage = true,
  variant = 'primary',
  size = 'medium',
  animated = true,
  className = ''
}) {
  const clampedProgress = Math.max(0, Math.min(100, progress));

  return (
    <div className={`progress-container ${className}`}>
      {message && (
        <div className="progress-message">{message}</div>
      )}
      
      <div className={`progress-bar ${variant} ${size} ${animated ? 'animated' : ''}`}>
        <div 
          className="progress-fill"
          style={{ width: `${clampedProgress}%` }}
          role="progressbar"
          aria-valuenow={clampedProgress}
          aria-valuemin="0"
          aria-valuemax="100"
        />
        
        {showPercentage && (
          <div className="progress-text">
            {Math.round(clampedProgress)}%
          </div>
        )}
      </div>
    </div>
  );
}

export default ProgressBar;