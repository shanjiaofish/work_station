import os
import cv2
import time
import shutil
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from cnocr import CnOcr
import easyocr
from pdf2image import convert_from_path
from paddleocr import PaddleOCR

from .base_service import BaseService
from models.exceptions import FileProcessingError, ValidationError
from config.config import get_config

# Import OCR parameters from the original param.py
try:
    from param import (
        fuel_keywords, fuel_mapping, fuel_fuzzy_mapping,
        invoice_number_pattern, date_pattern, quantity_pattern,
        quantity_fallback_pattern, simple_quantity_pattern,
        address_pattern, simple_address_pattern, district_keywords,
        extract_and_convert_date, extract_invoice_number, extract_quantity,
        roc_date_pattern, invoice_number_simple_pattern, invoice_number_mixed_pattern
    )
except ImportError:
    # Fallback values if param.py is not available
    fuel_keywords = ['汽油', '柴油', '天然氣']
    fuel_mapping = {'汽油': '汽油', '柴油': '柴油', '天然氣': '天然氣'}
    fuel_fuzzy_mapping = {}
    import re
    invoice_number_pattern = re.compile(r'\w{8}')
    date_pattern = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}')
    quantity_pattern = re.compile(r'(\d+\.?\d*)')
    quantity_fallback_pattern = re.compile(r'(\d+\.?\d*)')
    simple_quantity_pattern = re.compile(r'(\d+\.?\d*)')
    address_pattern = re.compile(r'.*號.*')
    district_keywords = ['市', '縣', '區', '鄉', '鎮']

class OCRService(BaseService):
    """Service for OCR operations"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.ocr_engines = {"cnocr": None, "easyocr": None, "paddleocr": None}
        
    def init_ocr_engines(self) -> None:
        """Initialize all OCR engines lazily"""
        if self.ocr_engines["cnocr"] is None:
            print("Initializing OCR engines (this may take a few minutes)...")
            try:
                self.ocr_engines["cnocr"] = CnOcr()
                self.ocr_engines["easyocr"] = easyocr.Reader(['ch_tra', 'en'])
                self.ocr_engines["paddleocr"] = PaddleOCR(use_angle_cls=False, lang='en')
                print("OCR engines initialized successfully!")
            except Exception as e:
                raise FileProcessingError(f"Failed to initialize OCR engines: {str(e)}")
    
    def process_pdf(self, pdf_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Process PDF file and extract invoice information"""
        if not os.path.exists(pdf_path):
            raise FileProcessingError(f"PDF file not found: {pdf_path}")
            
        if not pdf_path.lower().endswith('.pdf'):
            raise ValidationError("File must be a PDF")
        
        self.init_ocr_engines()
        
        try:
            print(f"Processing PDF: {pdf_path}")
            invoice_images = self._detect_invoices_from_pdf(pdf_path)
            print(f"Detected {len(invoice_images)} invoices, starting OCR recognition...")
            
            results = []
            for img_path in invoice_images:
                result = self._extract_invoice_info(img_path)
                results.append(result)
            
            # Generate report
            report_path = self._generate_excel_report(results)
            
            # Clean up temporary files
            self._cleanup_temp_files()
            
            return report_path, results
            
        except Exception as e:
            self._cleanup_temp_files()
            raise FileProcessingError(f"Failed to process PDF: {str(e)}")
    
    def _detect_invoices_from_pdf(self, pdf_path: str) -> List[str]:
        """Split PDF into individual invoice images"""
        os.makedirs(self.config.TEMP_IMG_FOLDER, exist_ok=True)
        os.makedirs(self.config.CROPPED_RECEIPTS_FOLDER, exist_ok=True)
        
        invoice_images = []
        
        try:
            images = convert_from_path(pdf_path, dpi=self.config.OCR_DPI)
            
            for i, img in enumerate(images):
                page_filename = f'page_{i + 1}.png'
                img_path = os.path.join(self.config.TEMP_IMG_FOLDER, page_filename)
                img.save(img_path, 'PNG')
                
                # Process image to find invoice regions
                image = cv2.imread(img_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Apply adaptive threshold
                bin_img = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15
                )
                
                # Calculate kernel size based on image dimensions
                height, width = gray.shape[:2]
                scale = max(width, height) / 1000
                ksize = int(30 * scale)
                ksize = max(20, min(ksize, 80))
                
                # Morphological operations to connect text
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
                dilated = cv2.dilate(bin_img, kernel, iterations=1)
                
                # Find contours
                contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filter contours by area
                boxes = [cv2.boundingRect(c) for c in contours 
                        if cv2.contourArea(c) > self.config.OCR_CONTOUR_AREA_THRESHOLD]
                
                # Sort boxes by position (top to bottom, left to right)
                boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
                
                # Crop individual invoices
                for j, (x, y, w, h) in enumerate(boxes):
                    crop_img = image[y:y + h, x:x + w]
                    crop_path = os.path.join(
                        self.config.CROPPED_RECEIPTS_FOLDER, 
                        f'{page_filename}_block{j}.png'
                    )
                    cv2.imwrite(crop_path, crop_img)
                    invoice_images.append(crop_path)
            
            return invoice_images
            
        except Exception as e:
            raise FileProcessingError(f"Failed to detect invoices from PDF: {str(e)}")
    
    def _extract_invoice_info(self, img_path: str) -> Dict[str, Any]:
        """Extract information from a single invoice image"""
        try:
            print(f"  > Processing image: {os.path.basename(img_path)}")

            # Use CnOCR for Chinese text
            cnocr_result = self.ocr_engines["cnocr"].ocr(img_path)
            cnocr_lines = [''.join(block['text']) for block in cnocr_result]

            # Use EasyOCR for mixed language text
            zh_lines = self.ocr_engines["easyocr"].readtext(img_path, detail=0)

            all_lines = cnocr_lines + zh_lines
            all_text_combined = ' '.join(all_lines)

            print(f"    > Extracted {len(all_lines)} text lines")

            # Initialize extracted fields
            invoice_number, date, quantity, fuel_type, address = None, None, None, None, None

            # Extract invoice number using new patterns
            for line in all_lines:
                if not invoice_number:
                    invoice_number = extract_invoice_number(line)
                    if invoice_number:
                        print(f"    > Found invoice number: {invoice_number}")
                        break

            # Extract date using new date conversion
            for line in all_lines:
                if not date:
                    date = extract_and_convert_date(line)
                    if date:
                        print(f"    > Found date: {date}")
                        break

            # Extract quantity using improved patterns
            for line in all_lines:
                if not quantity:
                    quantity = extract_quantity(line)
                    if quantity:
                        print(f"    > Found quantity: {quantity}")
                        break

            # Detect fuel type
            fuel_type = self._detect_fuel_type(all_text_combined)
            if fuel_type:
                print(f"    > Found fuel type: {fuel_type}")

            # Extract address using improved patterns
            for line in all_lines:
                if not address:
                    match = address_pattern.search(line)
                    if match:
                        address = line
                        print(f"    > Found address: {address}")
                        break

            # Fallback address detection
            if not address:
                for line in all_lines:
                    match = simple_address_pattern.search(line)
                    if match:
                        address = line
                        print(f"    > Found address (fallback): {address}")
                        break

            # Use PaddleOCR as fallback for missing information
            if not all([invoice_number, date, quantity, fuel_type]):
                print("    > Using PaddleOCR for missing information")
                invoice_number, date, quantity, fuel_type = self._extract_with_paddle_ocr(
                    img_path, invoice_number, date, quantity, fuel_type)

            # Clean extracted data
            address = self._clean_address(address) if address else None
            invoice_number = self._validate_invoice_number(invoice_number)
            date = self._validate_date(date)
            quantity = self._validate_quantity(quantity)
            fuel_type = self._validate_fuel_type(fuel_type)
            address = self._validate_address(address)

            print(f"    > Final results: Invoice={invoice_number}, Date={date}, Fuel={fuel_type}, Quantity={quantity}, Address={address[:50] if address else None}...")

            return {
                '頁數': os.path.basename(img_path),
                '發票號碼': invoice_number,
                '日期': date,
                '種類': fuel_type,
                '數量': quantity,
                '地址': address,
                '備註': ''
            }

        except Exception as e:
            print(f"Error extracting info from {img_path}: {str(e)}")
            return {
                '頁數': os.path.basename(img_path),
                '發票號碼': None, '日期': None, '種類': None,
                '數量': None, '地址': None, '備註': f'Processing error: {str(e)}'
            }
    
    def _detect_fuel_type(self, text_combined: str) -> str:
        """Detect fuel type from combined text"""
        matches = []
        
        # Apply fuzzy mappings
        for wrong, correct in fuel_fuzzy_mapping.items():
            text_combined = text_combined.replace(wrong, correct)
        
        # Find fuel keywords
        for fuel in fuel_keywords:
            if fuel in text_combined:
                mapped = fuel_mapping.get(fuel, fuel)
                matches.append((fuel, mapped))
        
        if matches:
            # Return the longest match (most specific)
            return sorted(matches, key=lambda x: -len(x[0]))[0][1]
        
        return None
    
    def _extract_with_paddle_ocr(self, img_path: str, invoice_number: str,
                                date: str, quantity: str, fuel_type: str) -> tuple:
        """Use PaddleOCR as fallback for missing information"""
        try:
            paddle_result = self.ocr_engines["paddleocr"].ocr(img_path)

            if paddle_result and paddle_result[0]:
                paddle_lines = [line[1][0] for line in paddle_result[0]]

                if not invoice_number:
                    for line in paddle_lines:
                        extracted = extract_invoice_number(line)
                        if extracted:
                            invoice_number = extracted
                            print(f"    > PaddleOCR found invoice number: {invoice_number}")
                            break

                if not date:
                    for line in paddle_lines:
                        extracted = extract_and_convert_date(line)
                        if extracted:
                            date = extracted
                            print(f"    > PaddleOCR found date: {date}")
                            break

                if not quantity:
                    for line in paddle_lines:
                        extracted = extract_quantity(line)
                        if extracted:
                            quantity = extracted
                            print(f"    > PaddleOCR found quantity: {quantity}")
                            break

                if not fuel_type:
                    text_joined = ' '.join(paddle_lines)
                    fuel_type = self._detect_fuel_type(text_joined)
                    if fuel_type:
                        print(f"    > PaddleOCR found fuel type: {fuel_type}")

            return invoice_number, date, quantity, fuel_type

        except Exception as e:
            print(f"PaddleOCR fallback failed: {str(e)}")
            return invoice_number, date, quantity, fuel_type
    
    def _clean_address(self, address: str) -> str:
        """Clean and correct address text"""
        if not address:
            return address
            
        replacements = {
            '半禹锈娜': '萬巒鄉', '号': '號', '锈': '', '娜': '',
            '潮洲': '潮州', '川': '州', '鎖': '鎮'
        }
        
        for wrong, right in replacements.items():
            address = address.replace(wrong, right)
        
        return address
    
    def _validate_invoice_number(self, invoice_number: str) -> str:
        """Validate invoice number format"""
        if not invoice_number:
            return None

        # Check against various patterns
        if (invoice_number_pattern.fullmatch(invoice_number) or
            invoice_number_simple_pattern.fullmatch(invoice_number) or
            invoice_number_mixed_pattern.fullmatch(invoice_number)):
            return invoice_number

        return invoice_number  # Return as-is if doesn't match, let user decide
    
    def _validate_date(self, date: str) -> str:
        """Validate date format"""
        if not date:
            return None

        # Date should already be in Western format from extract_and_convert_date
        if date_pattern.fullmatch(date):
            return date

        # Try to parse as valid date format
        try:
            from datetime import datetime
            datetime.strptime(date, '%Y-%m-%d')
            return date
        except ValueError:
            return date  # Return as-is if doesn't parse, let user decide
    
    def _validate_quantity(self, quantity: str) -> str:
        """Validate quantity is numeric"""
        if quantity:
            try:
                float(quantity)
                return quantity
            except ValueError:
                return None
        return quantity
    
    def _validate_fuel_type(self, fuel_type: str) -> str:
        """Validate fuel type is in allowed values"""
        if fuel_type and fuel_type not in fuel_mapping.values():
            return None
        return fuel_type
    
    def _validate_address(self, address: str) -> str:
        """Validate address format"""
        if not address:
            return None

        # Basic length check
        if len(address) < 5:
            return None

        # Check if it contains key address components
        has_location_marker = ('號' in address or '号' in address)
        has_district = any(city in address for city in district_keywords)
        has_road_marker = any(marker in address for marker in ['路', '街', '巷', '弄', '大道', '段'])

        # More flexible validation - at least 2 out of 3 criteria
        criteria_met = sum([has_location_marker, has_district, has_road_marker])

        if criteria_met >= 2:
            return address

        # If not enough criteria met, still return the address but let user decide
        return address
    
    def _generate_excel_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate Excel report from OCR results"""
        try:
            df = pd.DataFrame(results)
            
            report_filename = f'ocr_report_{int(time.time())}.xlsx'
            report_path = os.path.join(self.config.REPORTS_FOLDER, report_filename)
            
            # Ensure reports directory exists
            os.makedirs(self.config.REPORTS_FOLDER, exist_ok=True)
            
            df.to_excel(report_path, index=False)
            print(f"Report generated: {report_path}")
            
            return report_path
            
        except Exception as e:
            raise FileProcessingError(f"Failed to generate Excel report: {str(e)}")
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files and directories"""
        try:
            if os.path.exists(self.config.TEMP_IMG_FOLDER):
                shutil.rmtree(self.config.TEMP_IMG_FOLDER)
            
            if os.path.exists(self.config.CROPPED_RECEIPTS_FOLDER):
                shutil.rmtree(self.config.CROPPED_RECEIPTS_FOLDER)
                
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {str(e)}")