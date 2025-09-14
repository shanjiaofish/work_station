import logging
from flask import send_from_directory
from flask_restx import Namespace, Resource

from models.schemas import APISchemas
from utils.helpers import format_success_response, format_error_response
from config.config import get_config

logger = logging.getLogger(__name__)

def create_general_routes(api, db_client):
    """Create general routes namespace"""
    
    ns = api.namespace('general', description='General operations')
    config = get_config()
    
    # Create API models
    models = APISchemas.create_api_models(api)
    
    @ns.route('/hello')
    class HelloWorld(Resource):
        @ns.doc('hello_world')
        @ns.marshal_with(models['success_response'])
        @ns.response(500, 'Database connection failed', models['error'])
        def get(self):
            """Test API connection and database status"""
            try:
                if db_client:
                    # Test database connection
                    try:
                        # Simple query to test connection
                        response = db_client.table('materials').select('count', count='exact').limit(1).execute()
                        
                        return format_success_response(
                            data={"database_status": "connected"},
                            message="哈囉！我來自成功連線到 Supabase 的 Python 後端！"
                        )
                    except Exception as db_error:
                        logger.error(f"Database connection test failed: {str(db_error)}")
                        return format_error_response(
                            Exception("Database connection failed"), 500
                        )
                else:
                    return format_error_response(
                        Exception("Database client not initialized"), 500
                    )
                    
            except Exception as e:
                logger.error(f"Hello endpoint error: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/health')
    class HealthCheck(Resource):
        @ns.doc('health_check')
        @ns.marshal_with(models['success_response'])
        def get(self):
            """Health check endpoint"""
            try:
                health_status = {
                    "status": "healthy",
                    "version": "1.0.0",
                    "services": {
                        "database": "connected" if db_client else "disconnected",
                        "ocr": "available",
                        "google_maps": "available" if config.GOOGLE_MAPS_API_KEY else "unavailable"
                    },
                    "timestamp": "2025-01-01T00:00:00Z"  # You might want to use actual timestamp
                }
                
                return format_success_response(
                    data=health_status,
                    message="Service is healthy"
                )
                
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/info')
    class ServiceInfo(Resource):
        @ns.doc('service_info')
        @ns.marshal_with(models['success_response'])
        def get(self):
            """Get service information and available endpoints"""
            try:
                info = {
                    "name": "MFish Station Backend API",
                    "version": "1.0.0",
                    "description": "Backend API for MFish Station - OCR, Google Maps, and Material Management",
                    "endpoints": {
                        "materials": {
                            "search": "GET /api/materials/search",
                            "batch_match": "POST /api/materials/match-batch",
                            "create": "POST /api/materials",
                            "get": "GET /api/materials/{id}",
                            "update": "PUT /api/materials/{id}",
                            "delete": "DELETE /api/materials/{id}"
                        },
                        "ocr": {
                            "process_pdf": "POST /api/ocr/process-pdf",
                            "download_report": "GET /api/ocr/download-report/{filename}",
                            "status": "GET /api/ocr/status",
                            "reports": "GET /api/ocr/reports"
                        },
                        "gmap": {
                            "process": "POST /api/gmap/process",
                            "validate": "POST /api/gmap/validate-locations",
                            "geocode": "GET /api/gmap/geocode",
                            "download_excel": "GET /api/gmap/download/excel/{session_id}",
                            "download_zip": "GET /api/gmap/download/zip/{session_id}"
                        },
                        "general": {
                            "hello": "GET /api/general/hello",
                            "health": "GET /api/general/health",
                            "info": "GET /api/general/info"
                        }
                    },
                    "documentation": "/docs/"
                }
                
                return format_success_response(
                    data=info,
                    message="Service information retrieved successfully"
                )
                
            except Exception as e:
                logger.error(f"Service info error: {str(e)}")
                return format_error_response(e, 500)
    
    return ns

def create_static_routes(app):
    """Create routes for serving static files"""
    config = get_config()
    
    @app.route('/screenshots/<path:path>')
    def send_screenshot(path):
        """Serve screenshot files"""
        try:
            return send_from_directory(config.SCREENSHOTS_FOLDER, path)
        except Exception as e:
            logger.error(f"Error serving screenshot {path}: {str(e)}")
            return "File not found", 404