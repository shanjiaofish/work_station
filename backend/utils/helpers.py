import os
import time
import logging
import functools
from typing import Any, Dict, List
import werkzeug.utils
from flask import jsonify

logger = logging.getLogger(__name__)

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in allowed_extensions)

def secure_filename_with_timestamp(filename: str) -> str:
    """Generate secure filename with timestamp"""
    timestamp = int(time.time())
    secure_name = werkzeug.utils.secure_filename(filename)
    name, ext = os.path.splitext(secure_name)
    return f"{timestamp}_{name}{ext}"

def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if not"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def format_error_response(error: Exception, status_code: int = 500) -> Dict[str, Any]:
    """Format error response consistently"""
    return {
        "success": False,
        "error": str(error),
        "status_code": status_code
    }, status_code

def format_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Format success response consistently"""
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return response

def log_execution_time(func):
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate file size against maximum allowed size"""
    return file_size <= max_size

def sanitize_string(input_string: str) -> str:
    """Basic string sanitization"""
    if not isinstance(input_string, str):
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\0']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

def paginate_list(items: List[Any], page: int, per_page: int) -> Dict[str, Any]:
    """Paginate a list of items"""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "has_prev": page > 1,
        "has_next": page * per_page < total
    }

def extract_file_info(file) -> Dict[str, Any]:
    """Extract useful information from uploaded file"""
    if not file:
        return {}
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "content_length": file.content_length if hasattr(file, 'content_length') else None
    }

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if current_time - req_time < window]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(current_time)
            return True
        
        return False

def create_session_cache():
    """Create a simple session cache for storing temporary results"""
    return {}

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """Clean up old files in a directory"""
    if not os.path.exists(directory):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    cleaned_count += 1
                    logger.info(f"Cleaned up old file: {filepath}")
    
    except Exception as e:
        logger.error(f"Error cleaning up directory {directory}: {str(e)}")
    
    return cleaned_count