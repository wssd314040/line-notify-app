import streamlit as st
import os
from line_notify import send_line_notify
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 檔案

# 設置頁面配置
st.set_page_config(page_title="LINE Notify 圖片上傳", layout="centered")

# 確保上傳目錄存在
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 允許的文件類型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename(filename):
    # 簡單的文件名安全處理
    return ''.join(c for c in filename if c.isalnum() or c in '._-')

# 頁面標題
st.title('LINE Notify 圖片上傳')

# 檔案上傳
uploaded_file = st.file_uploader("選擇圖片", type=list(ALLOWED_EXTENSIONS))

# 訊息輸入
message = st.text_input("訊息", value="圖片上傳", help="請輸入訊息（若未輸入將使用預設訊息）")

# 發送按鈕
if st.button("上傳並發送"):
    if uploaded_file is None:
        st.error("請選擇檔案")
    else:
        try:
            # 保存上傳的文件
            filename = secure_filename(uploaded_file.name)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # 發送
            send_line_notify(filepath, message)
            st.success("發送成功！")
            
            # 清理文件
            if os.path.exists(filepath):
                os.remove(filepath)
                    
        except Exception as e:
            st.error(f"發送失敗：{str(e)}")
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)

# 顯示說明
st.markdown("""
### 使用說明
1. 選擇要上傳的圖片檔案
2. 輸入想要附加的訊息
3. 點擊「上傳並發送」按鈕
""") 