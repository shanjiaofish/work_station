#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import io
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api

# Setup encoding for Windows compatibility
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import configuration and utilities
from config.config import get_config
from models.exceptions import BaseAppException
from utils.helpers import format_error_response, ensure_directory_exists

# Import route modules
from routes.general_routes import create_general_routes, create_static_routes
from routes.material_routes import create_material_routes
from routes.ocr_routes import create_ocr_routes
from routes.gmap_routes import create_gmap_routes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    
    # Get configuration
    config = get_config()
    
    # Create Flask application
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Setup CORS
    CORS(app, origins=['*'])
    
    # Setup Swagger/OpenAPI
    api = Api(
        app,
        version='1.0',
        title='MFish Station Backend API',
        description='Refactored Backend API for MFish Station - OCR, Google Maps, and Material Management',
        doc='/docs/',
        prefix='/api'
    )
    
    # Initialize database client
    db_client = None
    try:
        from supabase_client import supabase
        db_client = supabase
        if db_client:
            logger.info("Database client initialized successfully")
        else:
            logger.warning("Database client is None - check Supabase configuration")
    except ImportError as e:
        logger.error(f"Failed to import Supabase client: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to initialize database client: {str(e)}")
    
    # Register route namespaces
    try:
        # General routes (health, info, hello)
        general_ns = create_general_routes(api, db_client)
        api.add_namespace(general_ns)
        
        # Material routes (search, batch match, CRUD)
        materials_ns = create_material_routes(api, db_client)
        api.add_namespace(materials_ns)
        
        # OCR routes (process PDF, download reports)
        try:
            ocr_ns = create_ocr_routes(api)
            api.add_namespace(ocr_ns)
            logger.info("OCR routes registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register OCR routes: {str(e)}")
        
        # Google Maps routes (process routes, geocoding)
        try:
            gmap_ns = create_gmap_routes(api)
            api.add_namespace(gmap_ns)
            logger.info("Google Maps routes registered successfully")
        except Exception as e:
            logger.warning(f"Failed to register Google Maps routes: {str(e)}")
        
        # Static file routes
        create_static_routes(app)
        
        logger.info("All route namespaces registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register routes: {str(e)}")
        raise
    
    # Global error handlers
    @app.errorhandler(BaseAppException)
    def handle_app_exception(error):
        """Handle custom application exceptions"""
        logger.error(f"Application error: {error.message}")
        return format_error_response(error, error.status_code)
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            "success": False,
            "error": "Resource not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {str(error)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred",
            "status_code": 500
        }), 500
    
    # Root endpoint
    @app.route('/')
    def index():
        """API root endpoint"""
        return jsonify({
            "name": "MFish Station Backend API",
            "version": "1.0.0",
            "status": "running",
            "message": "Refactored backend with improved architecture",
            "documentation": "/docs/",
            "health_check": "/api/general/health",
            "endpoints": {
                "general": "/api/general/",
                "materials": "/api/materials/",
                "ocr": "/api/ocr/",
                "gmap": "/api/gmap/"
            }
        })
    
    # Create necessary directories
    directories = [
        config.UPLOAD_FOLDER,
        config.SCREENSHOTS_FOLDER,
        config.REPORTS_FOLDER,
        config.TEMP_IMG_FOLDER,
        config.CROPPED_RECEIPTS_FOLDER
    ]
    
    for directory in directories:
        try:
            ensure_directory_exists(directory)
        except Exception as e:
            logger.warning(f"Failed to create directory {directory}: {str(e)}")
    
    return app

# Create application instance
app = create_app()

# Legacy route compatibility (to avoid breaking existing clients)
@app.route('/materials/match-batch', methods=['POST'])
def legacy_material_match():
    """Legacy endpoint for backward compatibility"""
    from flask import request
    try:
        from services.material_service import MaterialService
        from supabase_client import supabase
        
        if not supabase:
            return jsonify({"error": "Database connection failed"}), 500
        
        material_service = MaterialService(supabase)
        data = request.get_json()
        queries = data.get('queries', []) if data else []
        
        if not queries:
            return jsonify({"error": "No queries provided"}), 400
        
        results = material_service.batch_match_materials(queries)
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Legacy endpoint error: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("Starting MFish Station Backend API...")
    logger.info("Available at: http://localhost:8001")
    logger.info("API Documentation: http://localhost:8001/docs/")
    
    try:
        app.run(
            debug=get_config().DEBUG,
            port=8001,
            host='0.0.0.0'
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)