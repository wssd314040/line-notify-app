import time
import schedule
import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pytz import timezone
from datetime import datetime
from retrying import retry

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('screenshot_bot.log'),
        logging.StreamHandler()
    ]
)

# 修改 take_screenshot 函數
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def take_screenshot():
    driver = setup_driver()
    try:
        url = "https://www.example.com"
        driver.get(url)
        
        # 使用更可靠的等待機制
        driver.implicitly_wait(10)
        
        screenshot_path = f"screenshots/{datetime.now(tz).strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        send_line_notify(screenshot_path)
    except Exception as e:
        logging.error(f"截圖失敗: {str(e)}")
        raise
    finally:
        driver.quit()

# 修改 send_line_notify 函數
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def send_line_notify(image_path):
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": "Bearer Vjyk3QzUVyhhHw5AaFSm3i6EEdCfnD4k199r6B1JHD0"
    }
    data = {
        "message": f" 截圖完成！\n時間：{datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}"
    }
    try:
        with open(image_path, "rb") as image_file:
            files = {
                "imageFile": image_file
            }
            response = requests.post(url, headers=headers, data=data, files=files)
            if response.status_code == 200:
                logging.info("推播成功")
            else:
                logging.error(f"推播失敗: {response.text}")
                raise Exception("LINE Notify API 呼叫失敗")
    except Exception as e:
        logging.error(f"發送通知失敗: {str(e)}")
        raise

# 修改 job 函數
def job():
    try:
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"[{now}] 執行截圖任務...")
        take_screenshot()
    except Exception as e:
        logging.error(f"任務執行失敗: {str(e)}")

# 修改主程式
if __name__ == "__main__":
    logging.info("截圖機器人啟動中...")
    
    # 確保截圖儲存目錄存在
    import os
    os.makedirs("screenshots", exist_ok=True)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"主程式異常: {str(e)}")
            time.sleep(5)  # 發生錯誤時等待一段時間後繼續 