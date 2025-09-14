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
from utils.helpers import format_error_response

# Import route modules
from routes.general_routes import create_general_routes, create_static_routes
from routes.material_routes import create_material_routes

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
        title='MFish Station Backend API (Minimal)',
        description='Minimal Backend API for MFish Station - Materials Management Only',
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
        
        # Static file routes
        create_static_routes(app)
        
        logger.info("Core route namespaces registered successfully")
        
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
    
    # Root endpoint
    @app.route('/')
    def index():
        """API root endpoint"""
        return jsonify({
            "name": "MFish Station Backend API (Minimal)",
            "version": "1.0.0",
            "status": "running",
            "message": "Minimal backend with materials management only",
            "documentation": "/docs/",
            "health_check": "/api/general/health",
            "available_endpoints": {
                "general": "/api/general/",
                "materials": "/api/materials/"
            },
            "note": "OCR and Google Maps services require additional dependencies"
        })
    
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

@app.route('/materials/all', methods=['GET'])
def legacy_materials_all():
    """Legacy endpoint to get all materials"""
    try:
        from services.material_service import MaterialService
        from supabase_client import supabase
        
        if not supabase:
            return jsonify({"error": "Database connection failed"}), 500
        
        material_service = MaterialService(supabase)
        materials = material_service.list_materials(limit=1000)  # Get more materials for lookup page
        
        return jsonify(materials)
        
    except Exception as e:
        logger.error(f"Legacy materials all endpoint error: {str(e)}")
        return jsonify({"error": f"Failed to fetch materials: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("Starting MFish Station Backend API (Minimal)...")
    logger.info("Available at: http://localhost:8001")
    logger.info("API Documentation: http://localhost:8001/docs/")
    logger.info("Note: This minimal version includes materials management only")
    
    try:
        app.run(
            debug=get_config().DEBUG,
            port=8001,
            host='0.0.0.0'
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)