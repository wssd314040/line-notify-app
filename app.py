import streamlit as st
import os
from line_notify import send_line_notify
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import schedule
import time
import threading
import pytz

# 設置台北時區
taipei_tz = pytz.timezone('Asia/Taipei')

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
    st.session_state.last_send_time = datetime.now(taipei_tz)
if 'minute_count' not in st.session_state:
    st.session_state.minute_count = 0

def get_taipei_now():
    """獲取台北當前時間"""
    return datetime.now(taipei_tz)

def can_send_message():
    """檢查是否可以發送訊息"""
    now = get_taipei_now()
    time_since_last_send = (now - st.session_state.last_send_time).total_seconds()
    
    if time_since_last_send < 15:
        return False, f"請等待 {15 - int(time_since_last_send)} 秒後再試"
    
    if time_since_last_send >= 60:
        st.session_state.minute_count = 0
    
    if st.session_state.minute_count >= 3:
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

def scheduled_task(task_id, filepath, message):
    try:
        current_time = get_taipei_now()
        task_time = taipei_tz.localize(datetime.combine(schedule_date, schedule_time))
        
        # 移除時間檢查，讓 schedule 自己處理時間
        result = send_line_notify(filepath, message)
        if frequency == "一次性":
            if os.path.exists(filepath):
                os.remove(filepath)
            schedule.clear(task_id)
            if task_id in st.session_state.tasks:
                st.session_state.tasks.remove(task_id)
    except Exception as e:
        st.error(f"排程任務執行失敗: {str(e)}")
        if frequency == "一次性":
            if os.path.exists(filepath):
                os.remove(filepath)
            schedule.clear(task_id)

def schedule_sender():
    while True:
        schedule.run_pending()
        time.sleep(1)  # 每秒檢查一次

# 啟動排程執行緒（如果還沒啟動）
if 'scheduler_started' not in st.session_state:
    scheduler_thread = threading.Thread(target=schedule_sender, daemon=True)
    scheduler_thread.start()
    st.session_state.scheduler_started = True

# 頁面標題
st.title('LINE Notify 圖片上傳')

# 檔案上傳
uploaded_file = st.file_uploader("選擇圖片", type=list(ALLOWED_EXTENSIONS))

# 訊息輸入
message = st.text_input("訊息", value="圖片上傳", help="請輸入訊息（未輸入將使用預設訊息）")

# 發送方式選擇
schedule_type = st.radio("發送方式", ["立即發送", "定時發送"])

# 如果選擇定時發送，顯示日期和時間選擇器
schedule_date = None
schedule_time = None
if schedule_type == "定時發送":
    col1, col2 = st.columns(2)
    with col1:
        # 使用台北時間
        min_date = get_taipei_now().date()
        schedule_date = st.date_input("選擇期", min_value=min_date)
    with col2:
        schedule_time = st.time_input("選擇時間（精確到分鐘）")
        frequency = st.selectbox(
            "重複頻率",
            ["每天", "一次性"],
            index=1,
            help="選擇發送頻率（注意：LINE Notify 有發送頻率限制）"
        )

    # 檢查時間
    now = get_taipei_now()
    selected_datetime = taipei_tz.localize(datetime.combine(schedule_date, schedule_time))
    
    if selected_datetime <= now:
        st.warning("請選擇未來的時間")

# 修改定時發送的邏輯
def run_scheduled_task(filepath, message, schedule_time_str):
    while True:
        now = get_taipei_now()
        current_time_str = now.strftime("%H:%M")
        
        if current_time_str == schedule_time_str:
            try:
                result = send_line_notify(filepath, message)
                if os.path.exists(filepath):
                    os.remove(filepath)
                st.success(f"定時發送成功！時間: {current_time_str}")
                break
            except Exception as e:
                st.error(f"定時發送失敗: {str(e)}")
                break
        time.sleep(30)  # 每30秒檢查一次

# 修改定時發送部分
if schedule_type == "定時發送":
    if not schedule_time or not schedule_date:
        st.error("請選擇發送時間")
    else:
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
                
                now = get_taipei_now()
                selected_datetime = taipei_tz.localize(datetime.combine(schedule_date, schedule_time))
                
                if selected_datetime <= now:
                    st.error("請選擇未來的時間")
                else:
                    task_id = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    schedule_time_str = schedule_time.strftime("%H:%M")
                    
                    # 創建新的執行緒來運行定時任務
                    task_thread = threading.Thread(
                        target=run_scheduled_task,
                        args=(filepath, message, schedule_time_str),
                        daemon=True
                    )
                    task_thread.start()
                    
                    # 保存任務信息
                    if 'tasks' not in st.session_state:
                        st.session_state.tasks = {}
                    
                    st.session_state.tasks[task_id] = {
                        'filepath': filepath,
                        'message': message,
                        'schedule_time': schedule_time_str,
                        'thread': task_thread
                    }
                    
                    # 顯示確認訊息
                    time_until = selected_datetime - now
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)
                    
                    st.success(f"已排程在 {schedule_date.strftime('%Y-%m-%d')} {schedule_time_str} 發送 (約 {hours} 小時 {minutes} 分鐘後)")
            
            except Exception as e:
                st.error(f"處理失敗：{str(e)}")
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)

# 顯示當前任務
if 'tasks' in st.session_state and st.session_state.tasks:
    st.markdown("### 當前任務")
    for task_id, task_info in st.session_state.tasks.items():
        st.write(f"任務ID: {task_id}")
        st.write(f"預定時間: {task_info['schedule_time']}") 