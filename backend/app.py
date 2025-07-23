# work_station/backend/app.py

# --- 基礎與 Web 套件 ---
import os
import sys
import time
import datetime
import io
import zipfile
import re
import shutil
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import werkzeug.utils

# --- 功能性套件 ---
import googlemaps
from supabase_client import supabase

# --- OCR 相關套件 ---
import cv2
import numpy as np
from cnocr import CnOcr
import easyocr
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
# 從您原本的 OCR 工具導入設定變數
# 請確保 param.py 與 app.py 在同一個資料夾中
from param import *

# --- 解決 Flask 在 Windows 中 print() 可能產生的亂碼問題 ---
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ======================================================================
# --- 應用程式初始化與設定 (只需一次) ---
# ======================================================================
app = Flask(__name__)
CORS(app)

# --- 路徑設定 ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SCREENSHOTS_FOLDER'] = os.path.join(basedir, 'screenshots')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['REPORTS_FOLDER'] = os.path.join(basedir, 'reports')
app.config['TEMP_IMG_FOLDER'] = os.path.join(basedir, 'temp_imgs')
app.config['CROPPED_RECEIPTS_FOLDER'] = os.path.join(basedir, 'cropped_receipts')

# --- 全域物件 ---
GOOGLE_MAPS_API_KEY = os.getenv("Maps_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None
SESSION_RESULTS_CACHE = {}

# OCR 引擎 (延遲初始化)
ocr_engines = { "cnocr": None, "easyocr": None, "paddleocr": None }

# ======================================================================
# --- OCR 核心邏輯 (100% 移植自 gas_helper.py) ---
# ======================================================================

def init_ocr_engines():
    """初始化所有 OCR 引擎。"""
    if ocr_engines["cnocr"] is None:
        print("首次使用，正在初始化 OCR 引擎 (可能需要幾分鐘)...")
        ocr_engines["cnocr"] = CnOcr()
        ocr_engines["easyocr"] = easyocr.Reader(['ch_tra', 'en'])
        ocr_engines["paddleocr"] = PaddleOCR(use_angle_cls=False, lang='en')
        print("OCR 引擎初始化完成！")

def detect_invoices_from_pdf(pdf_path: str) -> list:
    """從 PDF 中分割出所有發票圖片。"""
    os.makedirs(app.config['TEMP_IMG_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CROPPED_RECEIPTS_FOLDER'], exist_ok=True)
    invoice_images = []
    images = convert_from_path(pdf_path, dpi=300)
    for i, img in enumerate(images):
        page_filename = f'page_{i + 1}.png'
        img_path = os.path.join(app.config['TEMP_IMG_FOLDER'], page_filename)
        img.save(img_path, 'PNG')
        image = cv2.imread(img_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        bin_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15)
        height, width = gray.shape[:2]
        scale = max(width, height) / 1000
        ksize = int(30 * scale)
        ksize = max(20, min(ksize, 80))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        dilated = cv2.dilate(bin_img, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 5000]
        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        for j, (x, y, w, h) in enumerate(boxes):
            crop_img = image[y:y + h, x:x + w]
            crop_path = os.path.join(app.config['CROPPED_RECEIPTS_FOLDER'], f'{page_filename}_block{j}.png')
            cv2.imwrite(crop_path, crop_img)
            invoice_images.append(crop_path)
    return invoice_images

def detect_fuel_type(text_combined: str) -> str:
    """從文字中偵測燃油種類。"""
    matches = []
    for wrong, correct in fuel_fuzzy_mapping.items():
        text_combined = text_combined.replace(wrong, correct)
    for fuel in fuel_keywords:
        if fuel in text_combined:
            mapped = fuel_mapping.get(fuel, fuel)
            matches.append((fuel, mapped))
    if matches:
        return sorted(matches, key=lambda x: -len(x[0]))[0][1]
    return None

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

# ======================================================================
# --- 輔助函式 ---
# ======================================================================
def get_origin_city(origin):
    """從完整的出發地地址中，提取出縣市名稱。"""
    city_keywords = ["台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市", "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣"]
    for city in city_keywords:
        if city in origin:
            return city
    return ""

# ======================================================================
# --- API 端點 (Endpoints) ---
# ======================================================================

@app.route('/api/hello', methods=['GET'])
def hello_world():
    if supabase: return jsonify({"message": "哈囉！我來自成功連線到 Supabase 的 Python 後端！"})
    else: return jsonify({"message": "資料庫連線失敗"}), 500

@app.route('/materials/match-batch', methods=['POST'])
def match_materials_batch():
    if not supabase: return jsonify({"error": "資料庫連線失敗"}), 500
    queries = request.get_json()
    if not queries: return jsonify({"error": "沒有收到任何查詢資料"}), 400
    all_results = []
    try:
        for index, original_name in enumerate(queries):
            # 使用正確的欄位名稱進行搜尋
            response = supabase.table('materials').select('material_id, material_name, carbon_footprint, declaration_unit').ilike('material_name', f'%{original_name}%').limit(5).execute()
            search_results = response.data if response.data else []
            all_results.append({ 
                "original_index": index, 
                "original_name": original_name, 
                "matches": search_results 
            })
        return jsonify(all_results)
    except Exception as e:
        print(f"批次比對時發生錯誤: {e}")
        return jsonify({"error": f"批次比對時發生錯誤: {e}"}), 500

@app.route('/api/gmap/process', methods=['POST'])
def gmap_process_api():
    if not gmaps: return jsonify({"error": "後端 Google Maps API 金鑰未設定。"}), 500
    data = request.get_json()
    origin, destinations_text = data.get('origin'), data.get('destinations', '')
    if not origin or not destinations_text: return jsonify({"error": "必須提供出發地和目的地。"}), 400
    destinations = [addr.strip() for addr in destinations_text.split('\n') if addr.strip()]
    results, session_id = [], f"session_{int(time.time())}"
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    image_folder_path = os.path.join(app.config['SCREENSHOTS_FOLDER'], today_str, session_id)
    os.makedirs(image_folder_path, exist_ok=True)
    origin_city = get_origin_city(origin)
    try:
        for idx, original_dest in enumerate(destinations):
            final_dest = original_dest
            if not any(char.isdigit() for char in final_dest) and origin_city and origin_city not in final_dest:
                final_dest = f"{origin_city} {final_dest}"
            directions_results = gmaps.directions(origin, final_dest, mode="driving", language="zh-TW", alternatives=True)
            if not directions_results: continue
            shortest_route = min(directions_results, key=lambda r: r['legs'][0]['distance']['value'])
            distance_text = shortest_route['legs'][0]['distance']['text']
            overview_polyline = shortest_route['overview_polyline']['points']
            image_content = b"".join(gmaps.static_map(
                size=(600, 400), scale=2, language='zh-TW', maptype='roadmap',
                path=f'enc:{overview_polyline}', markers=[f'color:red|label:O|{origin}', f'color:blue|label:D|{final_dest}']
            ))
            if image_content:
                safe_dest_name = "".join(c for c in final_dest if c.isalnum())[:20]
                image_filename = f"map_{idx}_{safe_dest_name}.png"
                image_path = os.path.join(image_folder_path, image_filename)
                with open(image_path, 'wb') as f: f.write(image_content)
                results.append({
                    "origin": origin, "destination": final_dest, "distance": distance_text,
                    "image_filename": image_filename, "image_local_path": image_path,
                    "screenshot_url": f"screenshots/{today_str}/{session_id}/{image_filename}"
                })
        SESSION_RESULTS_CACHE[session_id] = results
        return jsonify({"results": results, "session_id": session_id})
    except Exception as e:
        print(f"處理 Google Maps API 時發生嚴重錯誤: {e}")
        return jsonify({"error": f"處理時發生嚴重錯誤: {e}"}), 500

@app.route('/api/download/excel/<session_id>', methods=['GET'])
def download_excel(session_id):
    session_data = SESSION_RESULTS_CACHE.get(session_id)
    if not session_data: return "Session not found or expired.", 404
    export_data = [{"起始點": item['origin'], "終點": item['destination'], "距離": item['distance'], "圖片名稱": item['image_filename']} for item in session_data]
    df = pd.DataFrame(export_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name='路線距離報告')
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'google_maps_report_{session_id}.xlsx')

@app.route('/api/download/zip/<session_id>', methods=['GET'])
def download_zip(session_id):
    session_data = SESSION_RESULTS_CACHE.get(session_id)
    if not session_data: return "Session not found or expired.", 404
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in session_data: zf.write(item['image_local_path'], arcname=item['image_filename'])
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=f'map_images_{session_id}.zip')

@app.route('/screenshots/<path:path>')
def send_screenshot(path):
    return send_from_directory(app.config['SCREENSHOTS_FOLDER'], path)

@app.route('/api/ocr/process-pdf', methods=['POST'])
def ocr_process_api():
    if 'file' not in request.files: return jsonify({"error": "沒有找到檔案部分"}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'): return jsonify({"error": "未選擇或非 PDF 檔案"}), 400
    unique_filename = f"{int(time.time())}_{werkzeug.utils.secure_filename(file.filename)}"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(pdf_path)
    try:
        report_path, ocr_data = process_invoice_pdf(pdf_path)
        report_filename = os.path.basename(report_path)
        return jsonify({
            "message": "OCR 處理完成！",
            "download_url": f"api/download/ocr-report/{report_filename}",
            "data": ocr_data
        })
    except Exception as e:
        print(f"OCR 處理時發生錯誤: {e}")
        return jsonify({"error": f"處理失敗: {str(e)}"}), 500
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

@app.route('/api/download/ocr-report/<filename>')
def download_ocr_report(filename):
    return send_from_directory(app.config['REPORTS_FOLDER'], filename, as_attachment=True)

# --- 主程式進入點 ---
if __name__ == '__main__':
    for folder_key in ['SCREENSHOTS_FOLDER', 'UPLOAD_FOLDER', 'REPORTS_FOLDER', 'TEMP_IMG_FOLDER', 'CROPPED_RECEIPTS_FOLDER']:
        folder_path = app.config[folder_key]
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    app.run(debug=True, port=5000)
