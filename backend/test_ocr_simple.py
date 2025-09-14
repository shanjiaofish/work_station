#!/usr/bin/env python3
"""
Simple OCR test script using just EasyOCR
"""
import os
import sys
import cv2
import time
import shutil
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import easyocr
from pdf2image import convert_from_path

# Add the current directory to the path
sys.path.append(os.getcwd())

# Import our updated patterns and functions
from param import *
from config.config import get_config

def test_ocr_simple(pdf_path: str):
    """Test OCR with simplified approach using only EasyOCR"""

    print(f"Testing OCR with: {pdf_path}")

    config = get_config()

    # Create necessary directories
    os.makedirs(config.TEMP_IMG_FOLDER, exist_ok=True)
    os.makedirs(config.CROPPED_RECEIPTS_FOLDER, exist_ok=True)
    os.makedirs(config.REPORTS_FOLDER, exist_ok=True)

    try:
        # Convert PDF to images
        print("Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)
        print(f"Converted to {len(images)} images")

        # Initialize EasyOCR
        print("Initializing EasyOCR...")
        reader = easyocr.Reader(['ch_tra', 'en'])

        # Process each page to detect invoice regions
        all_invoice_images = []
        for i, img in enumerate(images):
            page_filename = f'page_{i + 1}.png'
            img_path = os.path.join(config.TEMP_IMG_FOLDER, page_filename)
            img.save(img_path, 'PNG')

            # Process image to find invoice regions (simplified approach)
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
                    if cv2.contourArea(c) > 5000]  # Using default threshold

            # Sort boxes by position (top to bottom, left to right)
            boxes = sorted(boxes, key=lambda b: (b[1], b[0]))

            print(f"Found {len(boxes)} potential invoice regions on page {i+1}")

            # Crop individual invoices
            for j, (x, y, w, h) in enumerate(boxes):
                crop_img = image[y:y + h, x:x + w]
                crop_path = os.path.join(
                    config.CROPPED_RECEIPTS_FOLDER,
                    f'{page_filename}_block{j}.png'
                )
                cv2.imwrite(crop_path, crop_img)
                all_invoice_images.append(crop_path)

        print(f"Total invoice regions detected: {len(all_invoice_images)}")

        # Extract information from each invoice region
        results = []
        for img_path in all_invoice_images:
            print(f"Processing: {os.path.basename(img_path)}")

            # Extract text using EasyOCR
            ocr_result = reader.readtext(img_path, detail=0)
            all_text = ' '.join(ocr_result)

            print(f"  Extracted {len(ocr_result)} text lines")

            # Use our extraction functions
            invoice_number = extract_invoice_number(all_text)
            date = extract_and_convert_date(all_text)
            quantity = extract_quantity(all_text)

            # Detect fuel type
            fuel_type = None
            for fuel in fuel_keywords:
                if fuel in all_text:
                    fuel_type = fuel_mapping.get(fuel, fuel)
                    break

            # Extract address (simplified)
            address = None
            for line in ocr_result:
                if any(keyword in line for keyword in district_keywords) and '號' in line:
                    address = line
                    break

            print(f"  Results: Invoice={invoice_number}, Date={date}, Fuel={fuel_type}, Quantity={quantity}")

            results.append({
                '頁數': os.path.basename(img_path),
                '發票號碼': invoice_number,
                '日期': date,
                '種類': fuel_type,
                '數量': quantity,
                '地址': address,
                '備註': ''
            })

        # Generate Excel report
        if results:
            df = pd.DataFrame(results)
            report_filename = f'ocr_report_{int(time.time())}.xlsx'
            report_path = os.path.join(config.REPORTS_FOLDER, report_filename)
            df.to_excel(report_path, index=False)
            print(f"Report generated: {report_path}")

            # Display results
            print("\\n=== RESULTS SUMMARY ===")
            for i, result in enumerate(results):
                print(f"\\nResult {i+1}:")
                for key, value in result.items():
                    print(f"  {key}: {value}")

            return report_path, results
        else:
            print("No results generated")
            return None, []

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, []

    finally:
        # Clean up temporary files
        try:
            if os.path.exists(config.TEMP_IMG_FOLDER):
                shutil.rmtree(config.TEMP_IMG_FOLDER)
            if os.path.exists(config.CROPPED_RECEIPTS_FOLDER):
                shutil.rmtree(config.CROPPED_RECEIPTS_FOLDER)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {str(e)}")

if __name__ == "__main__":
    pdf_path = '/Users/yangping/Studio/mfish/work_station/岡展-加油發票-1-3-3.pdf'
    test_ocr_simple(pdf_path)