def extract_invoice_info(img_path: str) -> dict:
    """從單張發票圖片中擷取資訊 (完整版)。"""
    cnocr_lines = [''.join(block['text']) for block in ocr_engines["cnocr"].ocr(img_path)]
    zh_lines = ocr_engines["easyocr"].readtext(img_path, detail=0)
    all_lines = cnocr_lines + zh_lines
    invoice_number, date, quantity, fuel_type, address = None, None, None, None, None

    for line in cnocr_lines:
        if not invoice_number and (match := invoice_number_pattern.search(line)): invoice_number = match.group()
        if not date and (match := date_pattern.search(line)): date = match.group()

    for i, line in enumerate(all_lines):
        if not quantity and any(k in line for k in fuel_keywords):
            if (match := quantity_pattern.search(line)): quantity = match.group(1); break
            if (match := quantity_fallback_pattern.search(line)): quantity = match.group(); break
            if i + 1 < len(all_lines):
                next_line = all_lines[i + 1]
                if (match := quantity_pattern.search(next_line)): quantity = match.group(1); break
                if (match := quantity_fallback_pattern.search(next_line)): quantity = match.group(); break

    if not quantity:
        for line in all_lines:
            if (match := quantity_pattern.search(line)): quantity = match.group(1); break

    all_text_combined = ' '.join(all_lines)
    fuel_type = detect_fuel_type(all_text_combined)

    for line in zh_lines:
        if not address and (match := address_pattern.search(line)): address = line; break
    if not address:
        for line in zh_lines:
            if any(keyword in line for keyword in district_keywords) and '號' in line and re.search(r'\d+', line): address = line; break

    # --- 關鍵：完整的 PaddleOCR 備用方案 ---
    if not all([invoice_number, date, quantity, fuel_type, address]):
        paddle_result = ocr_engines["paddleocr"].ocr(img_path) # 修正：移除 cls=False
        if paddle_result and paddle_result[0]:
            paddle_lines = [line[1][0] for line in paddle_result[0]]
            if not invoice_number:
                for line in paddle_lines:
                    if (match := invoice_number_pattern.search(line)): invoice_number = match.group(); break
            if not date:
                for line in paddle_lines:
                    if (match := date_pattern.search(line)): date = match.group(); break
            if not quantity:
                for line in paddle_lines:
                    if (match := simple_quantity_pattern.search(line)): quantity = match.group(1); break
            if not fuel_type:
                text_joined = ' '.join(paddle_lines)
                fuel_type = detect_fuel_type(text_joined)

    # --- 關鍵：完整的資料清理 ---
    if address:
        replacements = {'半禹锈娜': '萬巒鄉', '号': '號', '锈': '', '娜': '', '潮洲': '潮州', '川': '州', '鎖': '鎮'}
        for wrong, right in replacements.items(): address = address.replace(wrong, right)
    if invoice_number and not invoice_number_pattern.fullmatch(invoice_number): invoice_number = None
    if date and not date_pattern.fullmatch(date): date = None
    if quantity:
        try: float(quantity)
        except ValueError: quantity = None
    if fuel_type and fuel_type not in fuel_mapping.values(): fuel_type = None
    if address and (len(address) < 6 or '號' not in address or not any(city in address for city in district_keywords)): address = None

    print(f"  > OCR 結果: {invoice_number}, {date}, {fuel_type}, {quantity}, {address}")
    return {
        '頁數': os.path.basename(img_path), '發票號碼': invoice_number, '日期': date,
        '種類': fuel_type, '數量': quantity, '地址': address, '備註': ''
    }

def process_invoice_pdf(pdf_path: str) -> tuple[str, list]:
    """整合的 OCR 處理流程，回傳報告路徑和結果資料。"""
    init_ocr_engines()
    print(f"正在處理 PDF: {pdf_path}")
    invoice_images = detect_invoices_from_pdf(pdf_path)
    print(f"分割出 {len(invoice_images)} 張發票，開始 OCR 辨識...")
    results = [extract_invoice_info(img_path) for img_path in invoice_images]
    df = pd.DataFrame(results)
    report_filename = f'ocr_report_{int(time.time())}.xlsx'
    report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
    df.to_excel(report_path, index=False)
    print(f"報告已產生: {report_path}")
    if os.path.exists(app.config['TEMP_IMG_FOLDER']): shutil.rmtree(app.config['TEMP_IMG_FOLDER'])
    if os.path.exists(app.config['CROPPED_RECEIPTS_FOLDER']): shutil.rmtree(app.config['CROPPED_RECEIPTS_FOLDER'])
    return report_path, results