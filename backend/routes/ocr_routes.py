import os
import logging
from flask import request, send_from_directory
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

from services.ocr_service_fixed import OCRServiceFixed as OCRService
from models.exceptions import BaseAppException, ValidationError, FileProcessingError
from models.schemas import APISchemas
from utils.helpers import (
    format_error_response, format_success_response, 
    allowed_file, secure_filename_with_timestamp,
    ensure_directory_exists
)
from config.config import get_config

logger = logging.getLogger(__name__)

def create_ocr_routes(api):
    """Create OCR routes namespace"""
    
    ns = api.namespace('ocr', description='OCR processing operations')
    ocr_service = OCRService()
    config = get_config()
    
    # Create API models
    models = APISchemas.create_api_models(api)
    
    @ns.route('/process-pdf')
    class OCRProcessPDF(Resource):
        @ns.doc('ocr_process_pdf')
        @ns.expect(ns.parser().add_argument(
            'file', 
            location='files', 
            type='file', 
            required=True, 
            help='PDF file to process'
        ))
        @ns.marshal_with(models['ocr_response'])
        @ns.response(400, 'Invalid request', models['error'])
        @ns.response(422, 'File processing error', models['error'])
        @ns.response(500, 'Internal server error', models['error'])
        def post(self):
            """Process PDF file with OCR to extract invoice information"""
            try:
                # Check if file is in request
                if 'file' not in request.files:
                    raise ValidationError("No file part in request")
                
                file = request.files['file']
                
                # Validate file
                if file.filename == '':
                    raise ValidationError("No file selected")
                
                if not file.filename.lower().endswith('.pdf'):
                    raise ValidationError("File must be a PDF")
                
                if not allowed_file(file.filename, {'pdf'}):
                    raise ValidationError("Invalid file type")
                
                # Save uploaded file
                ensure_directory_exists(config.UPLOAD_FOLDER)
                unique_filename = secure_filename_with_timestamp(file.filename)
                pdf_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
                
                try:
                    file.save(pdf_path)
                    
                    # Process PDF with OCR
                    logger.info(f"Starting OCR processing for file: {unique_filename}")
                    report_path, ocr_data = ocr_service.process_pdf(pdf_path)
                    
                    report_filename = os.path.basename(report_path)
                    
                    logger.info(f"OCR processing completed. Report: {report_filename}")
                    
                    return {
                        "message": "OCR processing completed successfully!",
                        "download_url": f"api/ocr/download-report/{report_filename}",
                        "data": ocr_data,
                        "total_invoices": len(ocr_data),
                        "report_filename": report_filename
                    }
                    
                except Exception as e:
                    logger.error(f"OCR processing failed: {str(e)}")
                    raise FileProcessingError(f"OCR processing failed: {str(e)}")
                
                finally:
                    # Clean up uploaded file
                    if os.path.exists(pdf_path):
                        try:
                            os.remove(pdf_path)
                        except Exception as e:
                            logger.warning(f"Failed to clean up uploaded file: {str(e)}")
                
            except BaseAppException as e:
                logger.error(f"OCR processing error: {str(e)}")
                ns.abort(e.status_code, e.message)
            
            except Exception as e:
                logger.error(f"Unexpected error in OCR processing: {str(e)}")
                ns.abort(500, f"OCR processing failed: {str(e)}")
    
    @ns.route('/download-report/<string:filename>')
    class OCRDownloadReport(Resource):
        @ns.doc('download_ocr_report')
        @ns.response(404, 'Report not found')
        @ns.response(500, 'Internal server error')
        def get(self, filename):
            """Download OCR processing report"""
            try:
                # Security check: ensure filename is safe
                safe_filename = secure_filename(filename)
                
                if not safe_filename.endswith('.xlsx'):
                    ns.abort(400, "Invalid file type")
                
                report_path = os.path.join(config.REPORTS_FOLDER, safe_filename)
                
                if not os.path.exists(report_path):
                    ns.abort(404, "Report not found")
                
                return send_from_directory(
                    config.REPORTS_FOLDER, 
                    safe_filename, 
                    as_attachment=True
                )
                
            except Exception as e:
                logger.error(f"Error downloading report {filename}: {str(e)}")
                ns.abort(500, f"Failed to download report: {str(e)}")
    
    @ns.route('/status')
    class OCRStatus(Resource):
        @ns.doc('ocr_status')
        @ns.marshal_with(models['success_response'])
        def get(self):
            """Get OCR service status"""
            try:
                # Check if OCR engines are available
                status = {
                    "service": "available",
                    "engines": {
                        "cnocr": "available",
                        "easyocr": "available", 
                        "paddleocr": "available"
                    },
                    "supported_formats": ["pdf"],
                    "max_file_size": f"{config.MAX_CONTENT_LENGTH // (1024*1024)}MB"
                }
                
                return format_success_response(
                    data=status,
                    message="OCR service is operational"
                )
                
            except Exception as e:
                logger.error(f"Error checking OCR status: {str(e)}")
                return format_error_response(e, 500)
    
    @ns.route('/reports')
    class OCRReports(Resource):
        @ns.doc('list_ocr_reports')
        @ns.marshal_with(models['success_response'])
        def get(self):
            """List available OCR reports"""
            try:
                ensure_directory_exists(config.REPORTS_FOLDER)
                
                reports = []
                for filename in os.listdir(config.REPORTS_FOLDER):
                    if filename.endswith('.xlsx') and filename.startswith('ocr_report_'):
                        filepath = os.path.join(config.REPORTS_FOLDER, filename)
                        stat = os.stat(filepath)
                        
                        reports.append({
                            "filename": filename,
                            "size": stat.st_size,
                            "created": stat.st_ctime,
                            "download_url": f"api/ocr/download-report/{filename}"
                        })
                
                # Sort by creation time, newest first
                reports.sort(key=lambda x: x["created"], reverse=True)
                
                return format_success_response(
                    data=reports,
                    message=f"Found {len(reports)} OCR reports"
                )
                
            except Exception as e:
                logger.error(f"Error listing OCR reports: {str(e)}")
                return format_error_response(e, 500)
    
    return ns