import requests
import os

LINE_NOTIFY_TOKEN = os.getenv('LINE_NOTIFY_TOKEN')

def send_line_notify(image_path, message=""):
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"
    }
    
    # 如果沒有訊息，使用預設訊息
    if not message:
        message = "圖片上傳"
    
    data = {
        "message": "\n" + message
    }
    
    try:
        with open(image_path, "rb") as image_file:
            files = {
                "imageFile": image_file
            }
            response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code != 200:
                error_msg = response.json().get('message', '未知錯誤')
                raise Exception(f"LINE Notify API 呼叫失敗: {error_msg}")
            
            return response
    except Exception as e:
        raise Exception(f"發送失敗: {str(e)}") 