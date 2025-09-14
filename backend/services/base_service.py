import logging
from typing import Any, Optional
from models.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self, db_client=None):
        self.db = db_client
        
    def validate_required_fields(self, data: dict, required_fields: list) -> None:
        """Validate that all required fields are present"""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def handle_db_error(self, error: Exception, operation: str) -> None:
        """Handle database errors consistently"""
        logger.error(f"Database error during {operation}: {str(error)}")
        raise DatabaseError(f"Failed to {operation}")
    
    def safe_get(self, data: dict, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary"""
        return data.get(key, default)
    
    def format_response(self, data: Any, message: str = "Operation successful") -> dict:
        """Format successful response"""
        return {
            "success": True,
            "message": message,
            "data": data
        }