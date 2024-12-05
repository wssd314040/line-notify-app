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
    col1, col2 = st.columns(2)
    with col1:
        # 設置最小日期為今天
        min_date = datetime.now().date()
        schedule_date = st.date_input("選擇日期", min_value=min_date)
    with col2:
        # 使用 time_input 來選擇具體時間（包含分鐘）
        schedule_time = st.time_input("選擇時間（精確到分鐘）")
    
    # 檢查選擇的時間是否已過
    now = datetime.now()
    selected_datetime = datetime.combine(schedule_date, schedule_time)
    if selected_datetime <= now:
        st.warning("請選擇未來的時間")

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

            if schedule_type == "立即發送":
                # 立即發送
                response = send_line_notify(filepath, message)
                st.success("發送成功！")
                if os.path.exists(filepath):
                    os.remove(filepath)
            else:
                # 定時發送
                if not schedule_time or not schedule_date:
                    st.error("請選擇發送時間")
                else:
                    # 檢查時間是否有效
                    now = datetime.now()
                    selected_datetime = datetime.combine(schedule_date, schedule_time)
                    if selected_datetime <= now:
                        st.warning("請選擇未來的時間")
                    else:
                        # 設定排程任務
                        task_id = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        schedule_time_str = schedule_time.strftime("%H:%M")
                        
                        def scheduled_task(task_id, filepath, message):
                            try:
                                # 添加調試信息
                                st.write(f"執行排程任務: {task_id}")
                                st.write(f"檔案路徑: {filepath}")
                                st.write(f"訊息: {message}")
                                
                                result = send_line_notify(filepath, message)
                                st.write(f"發送結果: {result}")
                                
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                    st.write("檔案已刪除")
                                schedule.clear(task_id)
                            except Exception as e:
                                st.error(f"排程任務執行失敗: {str(e)}")
                        
                        # 設定排程時使用精確到分鐘的時間
                        if schedule_date == datetime.now().date():
                            schedule.every().day.at(schedule_time_str).do(
                                scheduled_task, task_id, filepath, message
                            ).tag(task_id)
                        else:
                            days_delay = (schedule_date - datetime.now().date()).days
                            schedule.every(days_delay).days.at(schedule_time_str).do(
                                scheduled_task, task_id, filepath, message
                            ).tag(task_id)
                        
                        freq_text = "一次" if frequency == "一次性" else frequency
                        st.success(f"已排程在 {schedule_date.strftime('%Y-%m-%d')} {schedule_time_str} 開始{freq_text}發送")
                    
        except Exception as e:
            st.error(f"發送失敗：{str(e)}")
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
   - 選擇重複頻率（一次性/每分鐘/每小時/每天）
5. 點擊「上傳並發送」按鈕
""") 