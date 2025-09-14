from flask_restx import fields

class APISchemas:
    """Central location for API schemas"""
    
    @staticmethod
    def create_api_models(api):
        # Error models
        error_model = api.model('Error', {
            'error': fields.String(required=True, description='Error message'),
            'status_code': fields.Integer(description='HTTP status code'),
            'payload': fields.Raw(description='Additional error details')
        })

        # Material models
        material_model = api.model('Material', {
            'material_id': fields.String(required=True, description='Material ID'),
            'material_name': fields.String(required=True, description='Material name'),
            'carbon_footprint': fields.Float(required=True, description='Carbon footprint value'),
            'declaration_unit': fields.String(required=True, description='Declaration unit'),
            'data_source': fields.String(description='Data source'),
            'life_cycle_scope': fields.String(description='Life cycle scope'),
            'announcement_year': fields.Integer(description='Announcement year'),
            'verified': fields.String(description='Verification status'),
            'remarks': fields.String(description='Additional remarks')
        })

        material_match_model = api.model('MaterialMatch', {
            'name': fields.String(required=True, description='Material name'),
            'id': fields.String(required=True, description='Material ID'),
            'carbon_footprint': fields.Float(required=True, description='Carbon footprint value'),
            'declaration_unit': fields.String(required=True, description='Declaration unit'),
            'score': fields.Float(required=True, description='Match score')
        })

        material_batch_result_model = api.model('MaterialBatchResult', {
            'query': fields.String(required=True, description='Original query'),
            'matches': fields.List(fields.Nested(material_match_model)),
            'default': fields.Integer(description='Default selection index')
        })

        material_queries_model = api.model('MaterialQueries', {
            'queries': fields.List(fields.String, required=True, description='List of material names to search')
        })

        # Google Maps models
        gmap_request_model = api.model('GMapRequest', {
            'origin': fields.String(required=True, description='Starting location'),
            'destinations': fields.String(required=True, description='Destinations (newline separated)')
        })

        gmap_result_model = api.model('GMapResult', {
            'origin': fields.String(required=True, description='Starting location'),
            'destination': fields.String(required=True, description='Destination'),
            'distance': fields.String(required=True, description='Distance information'),
            'image_filename': fields.String(description='Screenshot filename'),
            'screenshot_url': fields.String(description='Screenshot URL')
        })

        gmap_response_model = api.model('GMapResponse', {
            'results': fields.List(fields.Nested(gmap_result_model)),
            'session_id': fields.String(required=True, description='Session ID for downloads')
        })

        # OCR models
        ocr_result_model = api.model('OCRResult', {
            '頁數': fields.String(description='Page information'),
            '發票號碼': fields.String(description='Invoice number'),
            '日期': fields.String(description='Date'),
            '種類': fields.String(description='Fuel type'),
            '數量': fields.String(description='Quantity'),
            '地址': fields.String(description='Address'),
            '備註': fields.String(description='Remarks')
        })

        ocr_response_model = api.model('OCRResponse', {
            'message': fields.String(required=True, description='Processing status message'),
            'download_url': fields.String(required=True, description='Download URL for Excel report'),
            'data': fields.List(fields.Nested(ocr_result_model), description='OCR extracted data')
        })

        # Response wrapper
        success_response_model = api.model('SuccessResponse', {
            'success': fields.Boolean(default=True, description='Operation success status'),
            'message': fields.String(description='Success message'),
            'data': fields.Raw(description='Response data')
        })

        return {
            'error': error_model,
            'material': material_model,
            'material_match': material_match_model,
            'material_batch_result': material_batch_result_model,
            'material_queries': material_queries_model,
            'gmap_request': gmap_request_model,
            'gmap_result': gmap_result_model,
            'gmap_response': gmap_response_model,
            'ocr_result': ocr_result_model,
            'ocr_response': ocr_response_model,
            'success_response': success_response_model
        }