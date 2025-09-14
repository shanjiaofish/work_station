import os
import io
import zipfile
import logging
import pandas as pd
from flask import request, send_file
from flask_restx import Resource

from services.gmap_service import GMapService
from models.exceptions import BaseAppException, ValidationError
from models.schemas import APISchemas
from utils.helpers import format_error_response, format_success_response

logger = logging.getLogger(__name__)

# Session cache for storing results
SESSION_RESULTS_CACHE = {}

def create_gmap_routes(api):
    """Create Google Maps routes namespace"""
    
    ns = api.namespace('gmap', description='Google Maps operations')
    gmap_service = GMapService()
    
    # Create API models
    models = APISchemas.create_api_models(api)
    
    @ns.route('/process')
    class GMapProcess(Resource):
        @ns.doc('gmap_process')
        @ns.expect(models['gmap_request'])
        @ns.marshal_with(models['gmap_response'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(502, 'External service error', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def post(self):
            """Process Google Maps routes and generate screenshots"""
            try:
                if not request.is_json:
                    raise ValidationError("Request must contain JSON data")
                
                data = request.get_json()
                origin = data.get('origin', '').strip()
                destinations_text = data.get('destinations', '').strip()
                
                if not origin:
                    raise ValidationError("Origin location is required")
                
                if not destinations_text:
                    raise ValidationError("At least one destination is required")
                
                # Parse destinations
                destinations = [addr.strip() for addr in destinations_text.split('\n') 
                              if addr.strip()]
                
                if not destinations:
                    raise ValidationError("No valid destinations provided")
                
                logger.info(f"Processing {len(destinations)} routes from '{origin}'")
                
                # Process routes
                session_id, results = gmap_service.process_routes(origin, destinations)
                
                # Cache results for downloads
                SESSION_RESULTS_CACHE[session_id] = results
                
                logger.info(f"Route processing completed. Session ID: {session_id}")
                
                return {
                    "results": results,
                    "session_id": session_id,
                    "total_routes": len(results),
                    "origin": origin
                }
                
            except BaseAppException as e:
                logger.error(f"Google Maps processing error: {str(e)}")
                ns.abort(e.status_code, e.message)
            
            except Exception as e:
                logger.error(f"Unexpected error in Google Maps processing: {str(e)}")
                ns.abort(500, f"Route processing failed: {str(e)}")
    
    # Create location validation model
    location_validation_model = api.model('LocationValidationRequest', {
        'locations': api.fields.List(api.fields.String, required=True, description='List of locations to validate')
    })
    
    @ns.route('/validate-locations')
    class GMapValidateLocations(Resource):
        @ns.doc('validate_locations')
        @ns.expect(location_validation_model)
        @ns.marshal_with(models['success_response'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(502, 'External service error', models['error'])
        def post(self):
            """Validate that locations can be geocoded"""
            try:
                if not request.is_json:
                    raise ValidationError("Request must contain JSON data")
                
                data = request.get_json()
                locations = data.get('locations', [])
                
                if not locations or not isinstance(locations, list):
                    raise ValidationError("Locations list is required")
                
                results = gmap_service.validate_locations(locations)
                
                valid_count = sum(1 for r in results if r.get('valid', False))
                
                return format_success_response(
                    data=results,
                    message=f"Validated {len(locations)} locations. {valid_count} are valid."
                )
                
            except BaseAppException as e:
                logger.error(f"Location validation error: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error validating locations: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/geocode')
    class GMapGeocode(Resource):
        @ns.doc('geocode_address')
        @ns.param('address', 'Address to geocode', required=True)
        @ns.marshal_with(models['success_response'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(502, 'External service error', models['error'])
        def get(self):
            """Geocode an address to get coordinates"""
            try:
                address = request.args.get('address')
                
                if not address:
                    raise ValidationError("Address parameter is required")
                
                result = gmap_service.geocode_address(address)
                
                return format_success_response(
                    data=result,
                    message="Address geocoded successfully"
                )
                
            except BaseAppException as e:
                logger.error(f"Geocoding error: {str(e)}")
                return format_error_response(e, e.status_code)
            
            except Exception as e:
                logger.error(f"Unexpected error geocoding address: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/download/excel/<string:session_id>')
    class GMapDownloadExcel(Resource):
        @ns.doc('download_excel_report')
        @ns.response(404, 'Session not found')
        @ns.response(500, 'Internal server error')
        def get(self, session_id):
            """Download Excel report for a session"""
            try:
                session_data = SESSION_RESULTS_CACHE.get(session_id)
                
                if not session_data:
                    ns.abort(404, "Session not found or expired")
                
                # Prepare data for Excel export
                export_data = []
                for item in session_data:
                    export_data.append({
                        "起始點": item.get('origin', ''),
                        "終點": item.get('destination', ''),
                        "距離": item.get('distance', ''),
                        "圖片名稱": item.get('image_filename', ''),
                        "備註": item.get('remarks', '')
                    })
                
                # Create Excel file in memory
                df = pd.DataFrame(export_data)
                output = io.BytesIO()
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='路線距離報告')
                
                output.seek(0)
                
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'google_maps_report_{session_id}.xlsx'
                )
                
            except Exception as e:
                logger.error(f"Error downloading Excel for session {session_id}: {str(e)}")
                ns.abort(500, f"Failed to generate Excel report: {str(e)}")
    
    @ns.route('/download/zip/<string:session_id>')
    class GMapDownloadZip(Resource):
        @ns.doc('download_zip_images')
        @ns.response(404, 'Session not found')
        @ns.response(500, 'Internal server error')
        def get(self, session_id):
            """Download ZIP archive of route images"""
            try:
                session_data = SESSION_RESULTS_CACHE.get(session_id)
                
                if not session_data:
                    ns.abort(404, "Session not found or expired")
                
                # Create ZIP file in memory
                memory_file = io.BytesIO()
                
                with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for item in session_data:
                        image_path = item.get('image_local_path')
                        image_filename = item.get('image_filename')
                        
                        if image_path and image_filename and os.path.exists(image_path):
                            zf.write(image_path, arcname=image_filename)
                
                memory_file.seek(0)
                
                return send_file(
                    memory_file,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name=f'map_images_{session_id}.zip'
                )
                
            except Exception as e:
                logger.error(f"Error downloading ZIP for session {session_id}: {str(e)}")
                ns.abort(500, f"Failed to generate ZIP archive: {str(e)}")
    
    @ns.route('/sessions')
    class GMapSessions(Resource):
        @ns.doc('list_sessions')
        @ns.marshal_with(models['success_response'])
        def get(self):
            """List active sessions with their basic info"""
            try:
                sessions = []
                for session_id, results in SESSION_RESULTS_CACHE.items():
                    sessions.append({
                        "session_id": session_id,
                        "route_count": len(results),
                        "origin": results[0].get('origin', '') if results else '',
                        "has_images": any(item.get('image_filename') for item in results)
                    })
                
                return format_success_response(
                    data=sessions,
                    message=f"Found {len(sessions)} active sessions"
                )
                
            except Exception as e:
                logger.error(f"Error listing sessions: {str(e)}")
                return format_error_response(e, 500)
    
    return ns