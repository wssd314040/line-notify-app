import requests
import os

LINE_NOTIFY_TOKEN = "sr698Lzs4exMQYKNEzqVtj77mZ2Qwf2r9VUxl8JNLgx"

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
        # 檢查文件是否存在
        if not os.path.exists(image_path):
            raise Exception(f"找不到文件: {image_path}")
        
        # 檢查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > 3 * 1024 * 1024:  # 3MB
            raise Exception("文件大小超過限制 (最大3MB)")
            
        with open(image_path, "rb") as image_file:
            files = {
                "imageFile": ("image.jpg", image_file, "image/jpeg")
            }
            
            try:
                response = requests.post(url, headers=headers, data=data, files=files)
                response_json = response.json()
                
                if response.status_code != 200:
                    error_msg = response_json.get('message', '未知錯誤')
                    raise Exception(f"LINE Notify API 呼叫失敗: {error_msg} (狀態碼: {response.status_code})")
                
                return response_json
            except requests.exceptions.RequestException as e:
                raise Exception(f"網路請求失敗: {str(e)}")
            
    except Exception as e:
        raise Exception(f"發送失敗: {str(e)}") 