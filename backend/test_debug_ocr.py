#!/usr/bin/env python3
"""
Debug script to see exactly what OCR text is being extracted
"""
import os
import sys
import easyocr
from pdf2image import convert_from_path

sys.path.append(os.getcwd())
from param import extract_invoice_number

# Process the PDF and show what OCR text is extracted
pdf_path = '/Users/yangping/Studio/mfish/work_station/岡展-加油發票-1-3-3.pdf'
print(f"Testing OCR debug with: {pdf_path}")

# Convert to image
images = convert_from_path(pdf_path, dpi=300)
reader = easyocr.Reader(['ch_tra', 'en'])

# Process the full page first
print("\\n=== FULL PAGE OCR ===")
img_path = 'debug_full_page.png'
images[0].save(img_path, 'PNG')
full_page_text = reader.readtext(img_path, detail=0)

print("Full page OCR results (first 30 lines):")
for i, line in enumerate(full_page_text[:30]):
    print(f"{i+1:2d}: '{line}'")

print("\\n=== LOOKING FOR INVOICE NUMBERS ===")
# Look for all potential invoice numbers in full text
full_text = ' '.join(full_page_text)

# Find all patterns that could be invoice numbers
import re
patterns = [
    (r'[A-Z]{2}-\d{8}', 'Standard format (XX-12345678)'),
    (r'[A-Z]{2}\d{8}', 'Mixed format (XX12345678)'),
    (r'傳票號碼[：:]\s*(\d{7,8})', 'Voucher numbers'),
]

for pattern, description in patterns:
    matches = re.findall(pattern, full_text)
    if matches:
        print(f"{description}: {matches}")

# Test our extraction function
print(f"\\nOur extract_invoice_number function result: {extract_invoice_number(full_text)}")

# Clean up
os.remove(img_path)