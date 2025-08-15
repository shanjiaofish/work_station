#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import os
import datetime
import pandas as pd
import urllib.parse

# 解決輸出亂碼問題
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class GoogleMapsRobot:
    """Google Maps 自動化機器人類別"""
    
    def __init__(self, headless=True, window_size="1920,1080", lang="zh-TW"):
        """初始化機器人設定"""
        self.headless = headless
        self.window_size = window_size
        self.lang = lang
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """設定Chrome瀏覽器"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={self.window_size}")
        chrome_options.add_argument(f"--lang={self.lang}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 使用webdriver-manager自動管理ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def _teardown_driver(self):
        """關閉瀏覽器"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
    
    def resolve_address(self, destination, origin_city):
        """區名簡化轉換為「某市某區公所」"""
        # 若目的地包含數字（通常是詳細地址），不需處理
        if any(char.isdigit() for char in destination):
            return destination

        # 直轄市列表
        direct_cities = ["台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市"]

        # 特殊情況：只有區名但出發地是直轄市
        if destination.endswith("區"):
            if origin_city in direct_cities:
                return [f"{origin_city}{destination}公所", f"{destination}區公所"]
            else:
                # 非直轄市中的區，視為錯誤或模糊輸入，可用模糊查詢嘗試處理
                return [f"{destination}公所"]

        # 若是「斗六市」「北港鎮」「某鄉」等，直接加上「公所」
        if destination.endswith(("市", "鎮", "鄉")):
            return [f"{destination}公所"]

        # 其他模糊情況，直接原樣回傳
        return destination

    def _handle_cookies(self):
        """處理Google Maps的Cookie同意介面"""
        try:
            # 等待並尋找Cookie同意按鈕
            cookie_selectors = [
                "//button[contains(text(), '全部接受')]",
                "//button[contains(text(), 'Accept all')]", 
                "//button[contains(text(), '接受全部')]",
                "//button[contains(text(), '同意')]",
                "//button[contains(text(), 'Agree')]",
                "//button[@id='L2AGLb']",  # Google常用的接受按鈕ID
                "//div[contains(@class, 'QS5gu sy4vM')]//button[2]",  # Google Maps特定選擇器
                "//button[contains(@aria-label, 'Accept')]",
                "//button[contains(@data-value, 'Accept')]"
            ]
            
            # 嘗試點擊任何找到的Cookie同意按鈕
            for selector in cookie_selectors:
                try:
                    accept_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    accept_button.click()
                    print("✅ 已自動接受Cookie")
                    time.sleep(2)  # 等待頁面載入
                    return True
                except:
                    continue
            
            print("ℹ️ 未發現Cookie同意介面")
            return False
            
        except Exception as e:
            print(f"⚠️ 處理Cookie時發生錯誤: {e}")
            return False

    def get_origin_city(self, origin):
        """從完整的出發地地址中，提取出縣市名稱"""
        city_keywords = ["台北市", "新北市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市"]
        for city in city_keywords:
            if city in origin:
                return city
        return ""
    
    def query_single_route(self, origin, destination, screenshot_path=None):
        """查詢單一路線的距離和截圖"""
        encoded_origin = urllib.parse.quote(origin)
        encoded_destination = urllib.parse.quote(destination)

        url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={encoded_origin}"
            f"&destination={encoded_destination}"
            "&travelmode=driving"
        )

        print(f"查詢路線：{origin} -> {destination}")
        self.driver.get(url)
        time.sleep(8)

        try:
            route_blocks = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[starts-with(@id, 'section-directions-trip-')]")
                )
            )

            distances = []
            for block in route_blocks:
                try:
                    distance_elem = block.find_element(By.XPATH, ".//div[contains(text(), '公里') or contains(text(), 'km')]")
                    distance_text = distance_elem.text.strip()

                    if '公里' in distance_text:
                        km = float(distance_text.replace('公里', '').strip())
                    elif 'km' in distance_text:
                        km = float(distance_text.replace('km', '').strip())
                    else:
                        continue

                    distances.append((km, distance_text, block))
                except:
                    continue

            if distances:
                shortest = min(distances, key=lambda x: x[0])
                distance_text = shortest[1]
                route_element = shortest[2]

                print(f"✔ 取得最短距離：{distance_text}，點擊該路線")
                route_element.click()
                time.sleep(3)
            else:
                distance_text = "查無距離資訊"
                print("❌ 找不到距離資訊。")

        except Exception as e:
            distance_text = "查無距離資訊"
            print("❌ 擷取距離資訊失敗：", e)

        # 截圖
        if screenshot_path:
            self.driver.save_screenshot(screenshot_path)
            print(f"🖼️ 截圖儲存：{screenshot_path}")

        return distance_text
    
    def process_multiple_routes(self, origin, destinations, screenshot_folder=None):
        """處理多個目的地的路線查詢"""
        if not isinstance(destinations, list):
            destinations = [addr.strip() for addr in destinations.split('\n') if addr.strip()]
        
        results = []
        origin_city = self.get_origin_city(origin)
        
        # 設定截圖資料夾
        if screenshot_folder:
            os.makedirs(screenshot_folder, exist_ok=True)
        
        # 初始化瀏覽器
        self._setup_driver()
        
        # 先訪問Google Maps主頁處理Cookie（只需要做一次）
        try:
            self.driver.get("https://www.google.com/maps")
            self._handle_cookies()
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ 初始化Google Maps時發生錯誤: {e}")
        
        try:
            for idx, raw_dest in enumerate(destinations):
                resolved = self.resolve_address(raw_dest, origin_city)
                if isinstance(resolved, list):
                    print(f"❗ 地址「{raw_dest}」為區名，轉換為查詢公所：{resolved[0]}")
                    destination = resolved[0]
                else:
                    destination = resolved

                # 設定截圖路徑
                screenshot_path = None
                if screenshot_folder:
                    safe_dest_name = "".join(c for c in destination if c.isalnum())[:20]
                    screenshot_name = f"map_{idx}_{safe_dest_name}.png"
                    screenshot_path = os.path.join(screenshot_folder, screenshot_name)

                # 查詢路線
                distance_text = self.query_single_route(origin, destination, screenshot_path)

                # 收集結果
                result = {
                    "origin": origin,
                    "destination": destination,
                    "distance": distance_text,
                }
                
                if screenshot_path:
                    result["image_filename"] = os.path.basename(screenshot_path)
                    result["image_local_path"] = screenshot_path
                
                results.append(result)
                time.sleep(2)  # 避免過於頻繁的請求

        finally:
            # 清理瀏覽器
            self._teardown_driver()

        return results
    
    def process_from_excel(self, excel_file, address_column, origin, output_folder=None):
        """從Excel文件處理地址列表（保持向後兼容）"""
        df = pd.read_excel(excel_file)
        addresses = df[address_column].tolist()
        
        # 設定輸出資料夾
        if not output_folder:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            output_folder = f"{today}_距離截圖資訊"
        
        # 處理路線
        results = self.process_multiple_routes(origin, addresses, output_folder)
        
        # 儲存結果到CSV
        results_df = pd.DataFrame([{
            "目的地": result["destination"],
            "距離": result["distance"],
            "截圖檔名": result.get("image_local_path", "")
        } for result in results])
        
        csv_path = "google_maps_results.csv"
        results_df.to_csv(csv_path, index=False, encoding="utf_8_sig")
        print(f"\n✅ 所有查詢完成，結果已儲存於 {csv_path}")
        
        return results, csv_path

# 向後兼容的函式
def process_gmap_from_excel(excel_file, address_column, origin, output_folder=None):
    """向後兼容的函式"""
    robot = GoogleMapsRobot()
    return robot.process_from_excel(excel_file, address_column, origin, output_folder)

if __name__ == "__main__":
    # 測試用例
    robot = GoogleMapsRobot()
    results = robot.process_multiple_routes(
        origin="宜蘭縣南澳鄉蘇花路二段381號",
        destinations=["台北市信義區", "新北市板橋區", "桃園市中壢區"],
        screenshot_folder="test_screenshots"
    )
    print("測試結果：", results)