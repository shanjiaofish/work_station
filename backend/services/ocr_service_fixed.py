import os
import cv2
import time
import shutil
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import easyocr
from pdf2image import convert_from_path

from .base_service import BaseService
from models.exceptions import FileProcessingError, ValidationError
from config.config import get_config

# Import OCR parameters from the original param.py
try:
    from param import (
        fuel_keywords, fuel_mapping, fuel_fuzzy_mapping,
        address_pattern, simple_address_pattern, district_keywords,
        extract_and_convert_date, extract_invoice_number, extract_quantity
    )
except ImportError:
    # Fallback values if param.py is not available
    fuel_keywords = ['汽油', '柴油', '天然氣']
    fuel_mapping = {'汽油': '汽油', '柴油': '柴油', '天然氣': '天然氣'}
    fuel_fuzzy_mapping = {}
    import re
    address_pattern = re.compile(r'.*號.*')
    simple_address_pattern = re.compile(r'.*(市|縣).*(鄉|鎮|市|區).*\d+號?')
    district_keywords = ['市', '縣', '區', '鄉', '鎮']

class OCRServiceFixed(BaseService):
    """Fixed OCR Service using only EasyOCR"""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.ocr_engine = None

    def init_ocr_engine(self) -> None:
        """Initialize EasyOCR engine only"""
        if self.ocr_engine is None:
            print("Initializing OCR engine (EasyOCR)...")
            try:
                self.ocr_engine = easyocr.Reader(['ch_tra', 'en'])
                print("OCR engine initialized successfully!")
            except Exception as e:
                raise FileProcessingError(f"Failed to initialize OCR engine: {str(e)}")

    def process_pdf(self, pdf_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Process PDF file and extract invoice information"""
        if not os.path.exists(pdf_path):
            raise FileProcessingError(f"PDF file not found: {pdf_path}")

        if not pdf_path.lower().endswith('.pdf'):
            raise ValidationError("File must be a PDF")

        self.init_ocr_engine()

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

            # Use EasyOCR for text extraction
            ocr_result = self.ocr_engine.readtext(img_path, detail=0)
            all_text = ' '.join(ocr_result)

            print(f"    > Extracted {len(ocr_result)} text lines")

            # Initialize extracted fields
            invoice_number, date, quantity, fuel_type, address = None, None, None, None, None

            # Debug: Print first 20 lines of extracted text to see what we have
            print(f"    > First 10 OCR lines:")
            for i, line in enumerate(ocr_result[:10]):
                print(f"      {i+1}: '{line}'")

            # Extract invoice number using new patterns
            invoice_number = extract_invoice_number(all_text)
            if invoice_number:
                print(f"    > Found invoice number: {invoice_number}")
            else:
                print(f"    > No invoice number found in text: {all_text[:200]}...")

            # Extract date using new date conversion
            date = extract_and_convert_date(all_text)
            if date:
                print(f"    > Found date: {date}")

            # Extract quantity using improved patterns
            quantity = extract_quantity(all_text)
            if quantity:
                print(f"    > Found quantity: {quantity}")

            # Detect fuel type
            fuel_type = self._detect_fuel_type(all_text)
            if fuel_type:
                print(f"    > Found fuel type: {fuel_type}")

            # Extract address using improved patterns
            for line in ocr_result:
                if not address:
                    match = address_pattern.search(line)
                    if match:
                        address = line
                        print(f"    > Found address: {address}")
                        break

            # Fallback address detection
            if not address:
                for line in ocr_result:
                    match = simple_address_pattern.search(line)
                    if match:
                        address = line
                        print(f"    > Found address (fallback): {address}")
                        break

            # Clean extracted data
            address = self._clean_address(address) if address else None
            invoice_number = self._validate_invoice_number(invoice_number)
            date = self._validate_date(date)
            quantity = self._validate_quantity(quantity)
            fuel_type = self._validate_fuel_type(fuel_type)
            address = self._validate_address(address)

            print(f"    > Final results: Invoice={invoice_number}, Date={date}, Fuel={fuel_type}, Quantity={quantity}")

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
        return invoice_number  # Return as-is, let user decide

    def _validate_date(self, date: str) -> str:
        """Validate date format"""
        return date  # Return as-is, let user decide

    def _validate_quantity(self, quantity: str) -> str:
        """Validate quantity is numeric"""
        if quantity:
            try:
                float(quantity)
                return quantity
            except ValueError:
                return quantity  # Return as-is, let user decide
        return quantity

    def _validate_fuel_type(self, fuel_type: str) -> str:
        """Validate fuel type"""
        return fuel_type  # Return as-is, let user decide

    def _validate_address(self, address: str) -> str:
        """Validate address format"""
        return address  # Return as-is, let user decide

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