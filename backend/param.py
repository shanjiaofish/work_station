import re
from datetime import datetime

fuel_keywords = [
    '超级柴油','九五無鉛', '九二無鉛', '九八無鉛', '無鉛汽油', '超柴', '98號', '95號',
    '柴油', '九二', '九五', '九八', '92', '95', '98'
]
fuel_mapping = {
    '九五': '九五無鉛', '95': '九五無鉛', '九二': '九二無鉛', '92': '九二無鉛',
    '九八': '九八無鉛', '98': '九八無鉛', '超级柴油': '超級柴油', '超柴': '超級柴油',
    '柴油': '超級柴油',
}
fuel_fuzzy_mapping = {
    '無给': '無鉛', '无给': '無鉛', '無铅': '無鉛', '无铅': '無鉛', '柴油机': '柴油',
    '柴洒': '柴油', '超柴': '超級柴油', '超柴柴': '超級柴油', '九五無给': '九五無鉛',
    '九五無铅': '九五無鉛', '九二無给': '九二無鉛', '九八無给': '九八無鉛', '95+無给': '九五無鉛',
    '92+無给': '九二無鉛',  '98+無给': '九八無鉛', '超及柴油':'超級柴油', '超及柴油':'超級柴油'
}
district_keywords = ['台北', '台中', '高雄', '台南', '屏東', '新北', '桃園', '新竹', '宜蘭', '苗栗',
                     '彰化', '南投', '雲林', '嘉義', '台東', '花蓮', '金門', '連江', '澎湖']

# === 正則表達式預編譯 ===
# Invoice number patterns - handle multiple formats including OCR errors
invoice_number_pattern = re.compile(r'[A-Z]{2}-\d{8}')  # Standard format like KF-12345678
invoice_number_simple_pattern = re.compile(r'\d{7,8}')  # Simple numeric like 0118002
invoice_number_mixed_pattern = re.compile(r'[A-Z]{2}\d{8}')  # Mixed like JJ75925092

# OCR error-tolerant patterns - handle common OCR misreads
invoice_number_ocr_pattern = re.compile(r'([A-Z0-9|;%]{2})-?(\d{7,8})')  # Handle OCR errors, allow 7-8 digits

# Date patterns - handle both Western and ROC calendar
date_pattern = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}')  # Western: 2023-01-02
roc_date_pattern = re.compile(r'(\d{2,3})年(\d{1,2})[-/](\d{1,2})月')  # ROC: 112年01-02月
simple_date_pattern = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}')  # Flexible format

# Quantity patterns - handle various formats
quantity_pattern = re.compile(r'(\d+\.?\d*)\s*[lL公升]')  # With unit like 30.6L
quantity_fallback_pattern = re.compile(r'(\d+\.\d+)')  # Decimal numbers like 30.6
simple_quantity_pattern = re.compile(r'(\d+\.?\d*)')  # Any number format
quantity_with_context_pattern = re.compile(r'數量[:：]\s*(\d+\.?\d*)')  # With context

# Address patterns - more flexible matching
address_pattern = re.compile(
    r'(台北|新北|桃園|新竹|苗栗|台中|彰化|南投|雲林|嘉義|台南|高雄|屏東|宜蘭|花蓮|台東|澎湖|金門|連江)[縣市]?'
    r'.{0,15}(鄉|鎮|市|區).{0,30}(路|街|巷|弄|大道|段).{0,30}\d+([-\d]*號?|号)?'
)
# Simplified address pattern for fallback
simple_address_pattern = re.compile(r'.*(市|縣).*(鄉|鎮|市|區).*\d+號?')

# Gas station name patterns
station_name_pattern = re.compile(r'(.*加油站|.*油站|.*站)')

# Additional helper patterns
fuel_context_pattern = re.compile(r'(品名|商品|燃料)[:：]\s*(\S+)')
amount_pattern = re.compile(r'(金額|總額|合計)[:：]?\s*(\d+)')
tax_id_pattern = re.compile(r'統編[:：]?\s*(\d{8})')

# === Utility Functions ===

def correct_ocr_errors(text):
    """
    Correct common OCR errors in invoice numbers
    """
    corrected = text

    # Apply corrections in order of specificity (most specific first)
    specific_corrections = [
        ('|(F-', 'KF-'),      # |(F-26523895 -> KF-26523895
        ('|F-', 'KF-'),       # |F-26523895 -> KF-26523895
        (';0-%', 'KA-99'),    # ;0-%17734 -> KA-9917734
        ('00-', 'JJ-'),       # 00-75925092 -> JJ-75925092
        ('0-', 'J-'),         # 0- at start -> J-
    ]

    for wrong, right in specific_corrections:
        corrected = corrected.replace(wrong, right)

    # Then apply single character corrections
    char_corrections = {
        '%': '9',    # General % -> 9
        ';': 'K',    # ; -> K (if not already handled)
        '|': 'J',    # | -> J (if not already handled)
    }

    for wrong, right in char_corrections.items():
        corrected = corrected.replace(wrong, right)

    return corrected

def convert_roc_to_western_date(roc_year, month, day=None):
    """
    Convert ROC (Republic of China) calendar year to Western calendar date
    ROC year = Western year - 1911
    Example: ROC 112 = Western 2023
    """
    try:
        western_year = int(roc_year) + 1911
        month = int(month)

        # If day is not provided, use the first day of the month
        if day is None:
            day = 1
        else:
            day = int(day)

        # Validate month and day
        if month < 1 or month > 12:
            return None
        if day < 1 or day > 31:
            return None

        return f"{western_year:04d}-{month:02d}-{day:02d}"
    except (ValueError, TypeError):
        return None

def extract_and_convert_date(text):
    """
    Extract date from text and convert ROC format to Western format if needed
    """
    # Try ROC format first
    roc_match = roc_date_pattern.search(text)
    if roc_match:
        roc_year = roc_match.group(1)
        month = roc_match.group(2)
        day = roc_match.group(3) if len(roc_match.groups()) > 2 else None
        return convert_roc_to_western_date(roc_year, month, day)

    # Try standard Western format
    western_match = date_pattern.search(text)
    if western_match:
        return western_match.group()

    # Try simple date format
    simple_match = simple_date_pattern.search(text)
    if simple_match:
        return simple_match.group()

    return None

def extract_invoice_number(text):
    """
    Extract invoice number from text using multiple patterns
    Priority: Look for actual invoice numbers (JJ-12345678) not voucher numbers (傳票號碼)
    """
    # Apply OCR error correction first
    corrected_text = correct_ocr_errors(text)

    # Skip lines that contain the label "傳票號碼" as those are voucher numbers, not invoice numbers
    lines = corrected_text.split('\n') if '\n' in corrected_text else [corrected_text]

    for line in lines:
        # Skip lines that are just labels
        if line.strip() in ['傳票號碼', '傳票號碼：', '傳票號碼:']:
            continue

        # Skip lines that start with voucher number pattern (數字7-8位 without letters)
        if re.match(r'^\d{7,8}$', line.strip()):
            continue

        # Try standard format first (JJ-12345678, KF-12345678)
        match = invoice_number_pattern.search(line)
        if match:
            return match.group()

        # Try mixed format (JJ75925092 -> JJ-75925092)
        match = invoice_number_mixed_pattern.search(line)
        if match:
            result = match.group()
            # Convert to standard format
            if len(result) == 10 and result[:2].isalpha():
                return f"{result[:2]}-{result[2:]}"
            return result

        # Try OCR error-tolerant pattern
        match = invoice_number_ocr_pattern.search(line)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            # Return in standard format
            return f"{prefix}-{number}"

    # If no proper invoice number found, try the full text as fallback
    # Try standard format first (JJ-12345678, KF-12345678)
    match = invoice_number_pattern.search(corrected_text)
    if match:
        return match.group()

    # Try mixed format (JJ75925092 -> JJ-75925092)
    match = invoice_number_mixed_pattern.search(corrected_text)
    if match:
        result = match.group()
        # Convert to standard format
        if len(result) == 10 and result[:2].isalpha():
            return f"{result[:2]}-{result[2:]}"
        return result

    # Try OCR error-tolerant pattern on full text
    match = invoice_number_ocr_pattern.search(corrected_text)
    if match:
        prefix = match.group(1)
        number = match.group(2)
        # Return in standard format
        return f"{prefix}-{number}"

    return None

def extract_quantity(text):
    """
    Extract quantity from text using multiple patterns
    """
    # Try with unit context first
    match = quantity_with_context_pattern.search(text)
    if match:
        return match.group(1)

    # Try with L/公升 unit
    match = quantity_pattern.search(text)
    if match:
        return match.group(1)

    # Try decimal pattern
    match = quantity_fallback_pattern.search(text)
    if match:
        return match.group()

    # Try simple number pattern
    match = simple_quantity_pattern.search(text)
    if match:
        return match.group(1) if match.group(1) else match.group()

    return None