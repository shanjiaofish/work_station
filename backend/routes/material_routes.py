import logging
from flask import request
from flask_restx import Namespace, Resource
from werkzeug.exceptions import BadRequest

from services.material_service import MaterialService
from models.exceptions import BaseAppException, ValidationError
from models.schemas import APISchemas
from utils.helpers import format_error_response, format_success_response

logger = logging.getLogger(__name__)

def create_material_routes(api, db_client):
    """Create material routes namespace"""
    
    ns = api.namespace('materials', description='Material matching operations')
    material_service = MaterialService(db_client)
    
    # Create API models
    models = APISchemas.create_api_models(api)
    
    @ns.route('/search')
    class MaterialSearch(Resource):
        @ns.doc('search_materials')
        @ns.param('q', 'Search query', required=True)
        @ns.param('limit', 'Maximum results to return', type=int, default=5)
        @ns.marshal_with(models['success_response'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def get(self):
            """Search materials by name"""
            try:
                query = request.args.get('q')
                limit = int(request.args.get('limit', 5))
                
                if not query:
                    raise ValidationError("Search query 'q' parameter is required")
                
                results = material_service.search_materials(query, limit)
                
                return format_success_response(
                    data=results,
                    message=f"Found {len(results)} materials matching '{query}'"
                )
                
            except BaseAppException as e:
                logger.error(f"Material search error: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error in material search: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/match-batch')
    class MaterialMatchBatch(Resource):
        @ns.doc('match_materials_batch')
        @ns.expect(models['material_queries'])
        @ns.marshal_list_with(models['material_batch_result'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def post(self):
            """Batch match materials against database"""
            try:
                if not request.is_json:
                    raise ValidationError("Request must contain JSON data")
                
                data = request.get_json()
                queries = data.get('queries', []) if data else []
                
                if not queries:
                    raise ValidationError("No queries provided for batch matching")
                
                if not isinstance(queries, list):
                    raise ValidationError("Queries must be provided as a list")
                
                results = material_service.batch_match_materials(queries)
                
                logger.info(f"Successfully processed batch match for {len(queries)} queries")
                return results
                
            except BaseAppException as e:
                logger.error(f"Batch material matching error: {str(e)}")
                ns.abort(e.status_code, e.message)
            
            except Exception as e:
                logger.error(f"Unexpected error in batch matching: {str(e)}")
                ns.abort(500, f"Batch matching failed: {str(e)}")
    
    @ns.route('')
    class MaterialCollection(Resource):
        @ns.doc('get_materials')
        @ns.param('limit', 'Maximum number of materials to return', type=int, default=100)
        @ns.param('offset', 'Number of materials to skip', type=int, default=0)
        @ns.marshal_with(models['success_response'])
        def get(self):
            """Get list of materials"""
            try:
                limit = int(request.args.get('limit', 100))
                offset = int(request.args.get('offset', 0))
                
                # Validate parameters
                if limit > 1000:
                    limit = 1000  # Max limit
                if offset < 0:
                    offset = 0
                
                materials = material_service.list_materials(limit, offset)
                
                return format_success_response(
                    data=materials,
                    message=f"Retrieved {len(materials)} materials"
                )
                
            except Exception as e:
                logger.error(f"Error getting materials: {str(e)}")
                return format_error_response(e, 500)
        
        @ns.doc('create_material')
        @ns.expect(models['material'])
        @ns.marshal_with(models['success_response'])
        @ns.response(201, 'Material created successfully')
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def post(self):
            """Create a new material"""
            try:
                if not request.is_json:
                    raise ValidationError("Request must contain JSON data")
                
                material_data = request.get_json()
                if not material_data:
                    raise ValidationError("No material data provided")
                
                result = material_service.create_material(material_data)
                
                return format_success_response(
                    data=result,
                    message="Material created successfully"
                ), 201
                
            except BaseAppException as e:
                logger.error(f"Material creation error: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error creating material: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/<string:material_id>')
    class MaterialResource(Resource):
        @ns.doc('get_material')
        @ns.marshal_with(models['success_response'])
        @ns.response(404, 'Material not found', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def get(self, material_id):
            """Get material by ID"""
            try:
                result = material_service.get_material_by_id(material_id)
                
                return format_success_response(
                    data=result,
                    message="Material retrieved successfully"
                )
                
            except BaseAppException as e:
                logger.error(f"Error getting material {material_id}: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error getting material {material_id}: {str(e)}")
                return format_error_response(e, 500)
        
        @ns.doc('update_material')
        @ns.expect(models['material'])
        @ns.marshal_with(models['success_response'])
        @ns.response(404, 'Material not found', models['error'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def put(self, material_id):
            """Update material by ID"""
            try:
                if not request.is_json:
                    raise ValidationError("Request must contain JSON data")
                
                update_data = request.get_json()
                if not update_data:
                    raise ValidationError("No update data provided")
                
                result = material_service.update_material(material_id, update_data)
                
                return format_success_response(
                    data=result,
                    message="Material updated successfully"
                )
                
            except BaseAppException as e:
                logger.error(f"Error updating material {material_id}: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error updating material {material_id}: {str(e)}")
                return format_error_response(e, 500)
        
        @ns.doc('delete_material')
        @ns.marshal_with(models['success_response'])
        @ns.response(404, 'Material not found', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def delete(self, material_id):
            """Delete material by ID"""
            try:
                material_service.delete_material(material_id)
                
                return format_success_response(
                    message="Material deleted successfully"
                )
                
            except BaseAppException as e:
                logger.error(f"Error deleting material {material_id}: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error deleting material {material_id}: {str(e)}")
                return format_error_response(e, 500)
    
    return ns