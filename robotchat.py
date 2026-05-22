import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import asyncio
import logging
import hashlib
import re
import requests
import speech_recognition as sr
import mini.mini_sdk as MiniSdk
import socket
import threading
import http.server
import socketserver
import edge_tts

from mini.apis.api_setup import StartRunProgram
from mini.apis.api_action import PlayAction
from mini.apis.api_expression import PlayExpression
from mini.apis.api_sound import PlayAudio, ChangeRobotVolume
from mini.apis.api_behavior import StartBehavior, StopBehavior
from mini.apis import AudioStorageType

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
import json

SERIAL_NUMBER = "" # Mặc định trống, sẽ lấy từ file cấu hình của Web
config_path = os.path.join(os.path.dirname(__file__), "robot_config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
        SERIAL_NUMBER = config.get("SERIAL_NUMBER", "")
except:
    pass

TTS_CACHE_DIR = os.path.join(os.path.dirname(__file__), "tts_cache")
LANGUAGE      = "vi-VN"

logging.basicConfig(level=logging.WARNING)
MiniSdk.set_robot_type(MiniSdk.RobotType.EDU)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except: return '127.0.0.1'
    finally: s.close()

LOCAL_IP = get_local_ip()
HTTP_PORT = 8000 # Quay lại cổng 8000 ổn định

# Khởi chạy Máy chủ âm thanh (Dùng Threading để không bị treo)
def start_local_server():
    class RobustHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=TTS_CACHE_DIR, **kwargs)
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
        def log_message(self, *args): pass

    # Sử dụng ThreadingHTTPServer để xử lý đa luồng
    from http.server import ThreadingHTTPServer
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with ThreadingHTTPServer(("", HTTP_PORT), RobustHandler) as httpd:
            print(f"  📡 Audio Server: http://{LOCAL_IP}:{HTTP_PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"  ❌ Lỗi Server: {e}")

threading.Thread(target=start_local_server, daemon=True).start()

# ==========================================
# MICROPHONE
# ==========================================
recognizer = sr.Recognizer()
recognizer.energy_threshold = 1000
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.5       # Rút ngắn thời gian chờ dứt lời
recognizer.non_speaking_duration = 0.3

async def listen_mic():
    with sr.Microphone() as source:
        print("\n🎤 Đang lắng nghe...")
        try:
            # Bỏ lọc nhiễu tại đây để tăng tốc (đã lọc ở hàm main)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            return recognizer.recognize_google(audio, language=LANGUAGE)
        except: return ""

# ==========================================
# GIỌNG NÓI (BẢN FIX CUỐI CÙNG)
# ==========================================
async def robot_speak(text: str):
    if not text or len(text.strip()) < 2: return
    
    # Lọc bỏ tag cảm xúc
    clean_text = re.sub(r'EMOTION\s*:.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'\{[^}]*\}', '', clean_text).strip()
    if not clean_text: return

    try:
        filename = "v5_final_" + hashlib.md5(clean_text.encode()).hexdigest() + ".mp3"
        filepath = os.path.join(TTS_CACHE_DIR, filename)

        if not os.path.exists(filepath):
            await edge_tts.Communicate(clean_text, "vi-VN-HoaiMyNeural").save(filepath)
            await asyncio.sleep(0.3) # Đợi lâu hơn một chút để Windows thả file

        url = f"http://{LOCAL_IP}:{HTTP_PORT}/{filename}"
        print(f"🤖 Robot: {clean_text}")

        # Phát âm thanh trực tiếp (Bỏ StopAllAudio để tránh treo)
        await PlayAudio(url=url, storage_type=AudioStorageType.NET_PUBLIC, volume=1.0).execute()
        
        await asyncio.sleep(0.5 + len(clean_text) * 0.07)
    except Exception as e:
        print(f"❌ Lỗi giọng nói: {e}")

# ==========================================
# LỆNH DÁN CỨNG
# ==========================================
async def handle_special_commands(text: str) -> bool:
    cmd = text.lower()
    if any(k in cmd for k in ["chào", "hello", "hi"]):
        await PlayExpression(express_name="emo_016").execute()
        await robot_speak("Chào bạn nhé! Mình là Alpha Mini.")
        return True
    if any(k in cmd for k in ["bạn là ai", "tên gì"]):
        await robot_speak("Mình là Robot thông minh Alpha Mini.")
        return True
    if any(k in cmd for k in ["nhảy", "múa", "dance"]):
        await StartBehavior(name="dance_0004en").execute()
        await asyncio.sleep(8); await StopBehavior().execute()
        return True
    if any(k in cmd for k in ["hát", "sing"]):
        await StartBehavior(name="dance_0001en").execute()
        await asyncio.sleep(10); await StopBehavior().execute()
        return True
        
    # --- CÁC LỆNH MỚI THÊM ---
    if any(k in cmd for k in ["giỏi quá", "thông minh", "đẹp trai", "tuyệt vời", "khen"]):
        await PlayExpression(express_name="emo_004").execute() # Cười tít mắt / Trái tim
        await robot_speak("Hihi, cảm ơn bạn nhiều nha! Mình vui lắm đó.")
        return True
        
    if any(k in cmd for k in ["tập võ", "múa võ", "kungfu", "đánh võ"]):
        await PlayExpression(express_name="emo_014").execute() # Mắt nghiêm túc/chiến đấu
        await robot_speak("Chuẩn bị xem mình đi đường quyền đây! Ya da!")
        await PlayAction(action_name="action_018").execute() # Mã tập võ thường dùng của Alpha Mini
        return True

    if any(k in cmd for k in ["hít đất", "thể dục", "tập gym"]):
        await robot_speak("Mình là robot yêu thể thao đấy nhé. Nhìn mình hít đất đây!")
        await PlayAction(action_name="action_015").execute() # Mã hít đất thường dùng
        return True

    if any(k in cmd for k in ["chuyện cười", "kể chuyện", "buồn cười"]):
        await robot_speak("Bạn nghe nhé. Tại sao viên thuốc lại không bao giờ cười?... Vì nó bị... trầm cảm! Haha, đùa thôi.")
        await PlayExpression(express_name="emo_016").execute()
        return True
        
    if any(k in cmd for k in ["ngủ đi", "buồn ngủ", "mệt"]):
        await PlayExpression(express_name="emo_044").execute() # Mắt ngáp/nhắm
        await robot_speak("Oáp... Mình cũng buồn ngủ rồi, nhưng mình phải thức để trực hệ thống đây.")
        return True

    return False

# ==========================================
# MAIN LOOP
# ==========================================
async def main():
    print(f"📡 Đang tìm kiếm Robot: {SERIAL_NUMBER}")
    try:
        device = await MiniSdk.get_device_by_name(SERIAL_NUMBER, timeout=20)
        if not device: return
        
        await MiniSdk.connect(device)
        await StartRunProgram().execute()
        await ChangeRobotVolume(volume=1.0).execute()
        
        # Lọc nhiễu 1 lần duy nhất lúc khởi động để tiết kiệm thời gian cho các câu hỏi sau
        print("⚙️ Đang hiệu chỉnh Microphone...")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
        print("✅ Mic đã sẵn sàng!")
        
        await PlayExpression(express_name="emo_016").execute()
        await robot_speak("Sẵn sàng trò chuyện!")

        while True:
            question = await listen_mic()
            if not question: continue
            print(f"👤 Bạn: {question}")
            
            if any(k in question.lower() for k in ["thoát", "tạm biệt"]): break
            
            if await handle_special_commands(question): continue

            try:
                r = await asyncio.to_thread(requests.post, "http://127.0.0.1:8888/api/ask", json={"question": question}, timeout=5)
                data = r.json()
                if data.get("found_doc"):
                    # CỰC KỲ QUAN TRỌNG: Gọi hành động song song để không chặn giọng nói
                    await PlayExpression(express_name="emo_001").execute()
                    await robot_speak(data.get("answer", "Mình đã tìm thấy tài liệu."))
                else:
                    await robot_speak("Xin lỗi, mình không thấy thông tin này.")
            except:
                await robot_speak("Server đang bận.")

    except Exception as e: print(f"❌ Lỗi: {e}")
    finally:
        await MiniSdk.release()
        print("🔌 Ngắt kết nối.")

if __name__ == "__main__":
    asyncio.run(main())