import streamlit as st
import os
from line_notify import send_line_notify
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import schedule
import time
import threading

# 設置頁面配置
st.set_page_config(page_title="LINE Notify 圖片上傳", layout="centered")

# 確保上傳目錄存在
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 允許的文件類型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 初始化排程任務字典
if 'scheduled_tasks' not in st.session_state:
    st.session_state.scheduled_tasks = {}

# 在頂部添加限制計數器
if 'last_send_time' not in st.session_state:
    st.session_state.last_send_time = datetime.now()
if 'minute_count' not in st.session_state:
    st.session_state.minute_count = 0

def can_send_message():
    """檢查是否可以發送訊息"""
    now = datetime.now()
    # 檢查距離上次發送是否已經過了至少15秒
    time_since_last_send = (now - st.session_state.last_send_time).total_seconds()
    
    if time_since_last_send < 15:  # 至少等待15秒
        return False, f"請��待 {15 - int(time_since_last_send)} 秒後再試"
    
    # 重置每分鐘計數器
    if time_since_last_send >= 60:
        st.session_state.minute_count = 0
    
    # 檢查每分鐘限制
    if st.session_state.minute_count >= 3:  # 降低到每分鐘最多3則
        return False, "每分鐘最多發送3則訊息，請稍後再試"
    
    st.session_state.minute_count += 1
    st.session_state.last_send_time = now
    return True, ""

# 在發送訊息前檢查
def send_with_rate_limit(filepath, message):
    can_send, error_msg = can_send_message()
    if not can_send:
        raise Exception(error_msg)
    return send_line_notify(filepath, message)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def schedule_sender():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 啟動排程執行緒
scheduler_thread = threading.Thread(target=schedule_sender, daemon=True)
scheduler_thread.start()

# 頁面標題
st.title('LINE Notify 圖片上傳')

# 檔案上傳
uploaded_file = st.file_uploader("選擇圖片", type=list(ALLOWED_EXTENSIONS))

# 訊息輸入
message = st.text_input("訊息", value="圖片上傳", help="請輸入訊息（若未輸入將使用預設訊息）")

# 發送方式選擇
schedule_type = st.radio("發送方式", ["立即發送", "定時發送"])

# 如果選擇定時發送，顯示日期和時間選擇器
schedule_date = None
schedule_time = None
if schedule_type == "定時發送":
    col1, col2, col3 = st.columns(3)
    with col1:
        # 設置最小日期為今天
        min_date = datetime.now().date()
        schedule_date = st.date_input("選擇日期", min_value=min_date)
    with col2:
        schedule_time = st.time_input("選擇時間（精確到分鐘）")
    with col3:
        frequency = st.selectbox(
            "重複頻率",
            ["每天", "一次性"],  # 只保留每天和一次性選項
            index=1,  # 預設選擇"一次性"
            help="選擇發送頻率（注意：LINE Notify 有發送頻率限制）"
        )

    # 檢查選擇的時間是否已過
    now = datetime.now()
    selected_datetime = datetime.combine(schedule_date, schedule_time)
    if selected_datetime <= now and frequency == "一次性":
        st.warning("請選擇未來的時間")

# 顯示當前排程任務
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# 發送按鈕
if st.button("上傳並發送"):
    if uploaded_file is None:
        st.error("請選擇檔案")
    else:
        try:
            # 保存上傳的文件
            filename = secure_filename(uploaded_file.name)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # 確保上傳目錄存在
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # 保存文件
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 檢查文件是否成功保存
            if not os.path.exists(filepath):
                raise Exception("文件保存失敗")
            
            # 添加調試信息
            st.write(f"文件已保存到: {filepath}")
            st.write(f"文件大小: {os.path.getsize(filepath)} bytes")
            
            # 發送
            try:
                response = send_line_notify(filepath, message)
                st.success("發送成功！")
                st.write(f"API 回應: {response}")
            except Exception as e:
                st.error(f"發送失敗: {str(e)}")
                st.write("嘗試重新發送...")
                time.sleep(5)  # 等待5秒
                try:
                    response = send_line_notify(filepath, message)
                    st.success("重試發送成功！")
                except Exception as retry_e:
                    st.error(f"重試也失敗了: {str(retry_e)}")
            
            # 清理文件
            if os.path.exists(filepath):
                os.remove(filepath)
                st.write("文件已清理")
            
        except Exception as e:
            st.error(f"處理失敗：{str(e)}")
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)

# 顯示說明
st.markdown("""
### 使用說明
1. 選擇要上傳的圖片檔案
2. 輸入想要附加的訊息
3. 選擇發送方式（立即或定時）
4. 如果選擇定時發送：
   - 選擇日期和時間
   - 選擇重複頻率（每分鐘/每小時/每天/一次性）
5. 點擊「上傳並發送」按鈕
""")

# 顯示當前排程任務
if st.session_state.tasks:
    st.markdown("### 當前排程任務")
    for task_id in st.session_state.tasks:
        st.write(f"任務ID: {task_id}") 