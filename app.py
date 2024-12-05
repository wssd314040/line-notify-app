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
st.set_page_config(
    page_title="LINE Notify 圖片上傳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

# 初始化 session_state
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}

# 將 run_scheduled_task 函數移到文件最前面的函數定義區
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

# 在文件頂部添加自定義 CSS
st.markdown("""
<style>
    /* 整體容器樣式 */
    .main {
        max-width: 1000px;  /* 增加寬度 */
        margin: 0 auto;
        padding: 2rem;      /* 增加內邊距 */
    }
    
    /* 主標題樣式 */
    .main-title {
        color: #2c3e50;
        font-size: 2.2rem;  /* 增加字體大小 */
        font-weight: bold;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 分區塊標題樣式 */
    .section-title {
        color: #34495e;
        font-size: 1.5rem;  /* 增加字體大小 */
        font-weight: bold;
        margin: 1.5rem 0;
        padding-left: 1rem;
        border-left: 5px solid #3498db;
    }
    
    /* 任務卡片樣式 */
    .task-card {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }
    
    /* 輸入框和按鈕樣式 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stButton > button {
        font-size: 1.1rem;  /* 增加字體大小 */
        padding: 0.5rem 1rem;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.8rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
    }
    
    /* 輸入框樣式 */
    .stTextInput>div>div>input {
        font-size: 0.9rem;
        padding: 0.4rem 0.8rem;
    }
    
    /* 分隔線樣式 */
    hr {
        margin: 1rem 0;
        border: none;
        border-top: 1px solid #eee;
    }
    
    /* 調整間距 */
    .stRadio>div {
        margin-bottom: 0.5rem;
    }
    
    .stSelectbox>div>div {
        padding: 0.3rem;
    }
    
    /* 提示訊息樣式 */
    .success-msg {
        padding: 0.5rem;
        background-color: #d4edda;
        border-radius: 4px;
        color: #155724;
        font-size: 0.9rem;
    }
    
    .error-msg {
        padding: 0.5rem;
        background-color: #f8d7da;
        border-radius: 4px;
        color: #721c24;
        font-size: 0.9rem;
    }
    
    /* 自定義容器 */
    .custom-container {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.5rem 0;
    }
    
    /* 隱藏 Streamlit 預設的漢堡選單 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 使用自定義容器包裝內容
st.markdown('<div class="main">', unsafe_allow_html=True)

# 主標題
st.markdown('<h1 class="main-title">LINE Notify 圖片上傳</h1>', unsafe_allow_html=True)

# 文件上傳區塊
with st.container():
    st.markdown('<h2 class="section-title">📁 檔案上傳</h2>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("選擇圖片", type=list(ALLOWED_EXTENSIONS))

# 訊息和發送設定區塊
col1, col2 = st.columns(2)
with col1:
    st.markdown('<h2 class="section-title">✍️ 訊息</h2>', unsafe_allow_html=True)
    message = st.text_input("", value="圖片上傳", help="請輸入訊息")

with col2:
    st.markdown('<h2 class="section-title">⚙️ 發送方式</h2>', unsafe_allow_html=True)
    schedule_type = st.radio("", ["立即發送", "定時發送"])

# 修改定時設定區塊部分
if schedule_type == "定時發送":
    col1, col2 = st.columns(2)
    with col1:
        min_date = get_taipei_now().date()
        schedule_date = st.date_input("日期", min_value=min_date)
    with col2:
        schedule_time = st.time_input("時間")
        frequency = st.selectbox(
            "重複頻率",
            ["每天", "一次性"],
            index=1,
            help="選擇發送頻率（注意：LINE Notify 有發送頻率限制）"
        )

# 直接顯示上傳按鈕（移除空白區域）
if st.button("上傳並發送", use_container_width=True):
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
            
            if schedule_type == "立即發送":
                # 立即發送
                try:
                    response = send_line_notify(filepath, message)
                    st.success("發送成功！")
                except Exception as e:
                    st.error(f"發送失敗: {str(e)}")
                finally:
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                # 定時發送
                if not schedule_time or not schedule_date:
                    st.error("請選擇發送時間")
                else:
                    # 檢查時間是否有效
                    now = get_taipei_now()
                    selected_datetime = taipei_tz.localize(datetime.combine(schedule_date, schedule_time))
                    if selected_datetime <= now:
                        st.error("請選擇未來的時間")
                        if os.path.exists(filepath):
                            os.remove(filepath)
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

# 當前任務顯示
if st.session_state.tasks:
    st.markdown('<h2 class="section-title">📋 進行中的任務</h2>', unsafe_allow_html=True)
    for task_id, task_info in st.session_state.tasks.items():
        st.markdown(f"""
        <div class="task-card">
            <small>任務ID: {task_id}</small><br>
            預定時間: {task_info['schedule_time']}
        </div>
        """, unsafe_allow_html=True)

# 使用說明（收合式）
with st.expander("💡 使用說明"):
    st.markdown("""
    1. 選擇圖片檔案
    2. 輸入訊息
    3. 選擇發送方式
    4. 定時發送需設定時間
    5. 點擊發送按鈕
    """)

st.markdown('</div>', unsafe_allow_html=True)

# 將 run_scheduled_task 函數移到文件頂部
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

# 顯示當前任務
if st.session_state.tasks:
    st.markdown("### 當前任務")
    for task_id, task_info in st.session_state.tasks.items():
        st.write(f"任務ID: {task_id}")
        st.write(f"預定時間: {task_info['schedule_time']}") 