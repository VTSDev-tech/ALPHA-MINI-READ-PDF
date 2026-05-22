import os
import sys
import asyncio
import json
import subprocess
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import fitz  # PyMuPDF
from ingest_pdf import process_pdfs
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

# ==========================================
# CẤU HÌNH
# ==========================================
load_dotenv()
CHROMA_PATH = "chroma_db"

# Lấy đường dẫn thư mục gốc của project (nơi chứa server.py)
BASE_DIR = Path(__file__).resolve().parent

PDF_SRC_DIR = BASE_DIR / "TAI_LIEU_PDF" # Cập nhật theo đúng tên thư mục bên Bangiao
PAGE_IMG_DIR = BASE_DIR / "web_view" / "pdf_pages"
PAGE_IMG_DIR.mkdir(parents=True, exist_ok=True)

embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings_model)
print("✅ Đã kết nối ChromaDB Offline. Sẵn sàng!")

def render_pdf_page(source_filename: str, page_num: int) -> str:
    try:
        pdf_path = PDF_SRC_DIR / source_filename
        img_name = f"{source_filename}_page{page_num}.jpg"
        img_path = PAGE_IMG_DIR / img_name
        if not img_path.exists():
            doc = fitz.open(str(pdf_path))
            page = doc[page_num - 1]
            # Tối ưu: Giảm tỷ lệ matrix xuống 1.5 và dùng JPEG 80% để load Web siêu tốc (giảm 90% dung lượng)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            pix.save(str(img_path), "jpeg", jpg_quality=80)
            doc.close()
        return f"/pdf_pages/{img_name}"
    except Exception as e: 
        print(f"❌ Lỗi tạo ảnh PDF: {e}")
        return None

# ==========================================
# FASTAPI
# ==========================================
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/pdf_pages", StaticFiles(directory=str(PAGE_IMG_DIR)), name="pdf_pages")

class ConnectionManager:
    def __init__(self): self.active = []
    async def connect(self, ws): await ws.accept(); self.active.append(ws)
    def disconnect(self, ws): 
        if ws in self.active: self.active.remove(ws)
    async def broadcast(self, data):
        for c in self.active:
            try: await c.send_json(data)
            except: pass

manager = ConnectionManager()
last_state = {"type": "idle"}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try: await ws.send_json(last_state)
    except: pass
    try:
        while True: await ws.receive_text()
    except: manager.disconnect(ws)

class AskRequest(BaseModel):
    question: str

@app.post("/api/ask")
async def ask_rag(req: AskRequest):
    print(f"🔍 Tìm kiếm: {req.question}")
    try:
        # Tối ưu tìm kiếm: Thêm trọng số cho từ khóa quan trọng
        tu_khoa_uu_tien = ["giá", "chi phí", "vnđ", "bảng giá", "bao nhiêu", "kpi", "cam kết", "kiến trúc", "sơ đồ", "ưu điểm", "khác biệt"]
        cau_hoi_lower = req.question.lower()
        
        # Gọi Chroma tìm 5 kết quả tốt nhất
        docs = await asyncio.to_thread(db.similarity_search_with_relevance_scores, req.question, k=5)
        
        if not docs: return {"answer": "", "found_doc": False}
        
        best_match = None; best_score = -1.0
        
        for doc, score in docs:
            doc_text_lower = doc.page_content.lower()
            for tu in tu_khoa_uu_tien:
                if tu in cau_hoi_lower and tu in doc_text_lower:
                    score += 0.15 # Tăng 15% độ ưu tiên
            
            if score > best_score:
                best_score = score; best_match = doc

        print(f"  🎯 Điểm khớp Chroma tối ưu: {best_score:.4f}")

        if best_match and best_score > 0.45:
            source = best_match.metadata.get("source", "unknown")
            page = best_match.metadata.get("page", 0) + 1
            text = best_match.page_content
            img_url_rel = await asyncio.to_thread(render_pdf_page, source, page)
            
            payload = {
                "type": "document", "file_name": source, "page": f"Trang {page}",
                "image_url": img_url_rel if img_url_rel else "",
                "insights": [l.strip() for l in text.split("\n") if l.strip()][:3]
            }
            global last_state; last_state = payload
            await manager.broadcast(payload)
            import random
            cau_tra_loi_ngau_nhien = [
                "Đây là thông tin mình tìm được, mời bạn xem trên màn hình nhé!",
                "Mình đã tìm thấy nội dung bạn cần rồi đó, mời bạn nhìn qua Tivi nha.",
                "Dạ, tài liệu liên quan đang hiển thị trên màn hình cho bạn rồi nè.",
                "Thông tin này có trong tài liệu, mình đã mở sẵn trên màn hình cho bạn rồi.",
                "Mình đã tra cứu xong, mời bạn xem chi tiết trên màn hình Dashboard nhé.",
                "Đây là trang tài liệu khớp nhất với câu hỏi của bạn, mời bạn xem.",
                "Mình đã tìm thấy rồi! Nội dung đang hiện trên màn hình Tivi cho bạn đó.",
                "Mời bạn nhìn lên màn hình, mình đã tìm thấy thông tin bạn cần rồi nè.",
                "Dữ liệu bạn yêu cầu đã được trình chiếu lên màn hình, bạn xem nhé!",
                "Của bạn đây! Mọi thông tin chi tiết đang ở trên màn hình Dashboard."
            ]
            chosen_answer = random.choice(cau_tra_loi_ngau_nhien)
            
            return {"answer": f"{chosen_answer} EMOTION:{{\"cam_xuc\":\"emo_001\",\"action\":\"\"}}", "found_doc": True, "text": text}

        return {"answer": "", "found_doc": False}
    except Exception as e:
        print(f"❌ Lỗi: {e}"); return {"answer": "", "found_doc": False}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    print(f"📥 Đang nhận file: {file.filename}")
    try:
        file_path = PDF_SRC_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        print("⏳ Đang nạp dữ liệu vào AI...")
        # Chỉ nạp đúng file vừa tải lên để tránh trùng lặp
        await asyncio.to_thread(process_pdfs, str(file_path))
        
        return {"message": f"Tải lên {file.filename} thành công!"}
    except Exception as e:
        print(f"❌ Lỗi Upload: {e}")
        return {"error": str(e)}

@app.post("/api/sync")
async def sync_ai_data():
    global db
    print("🔄 Bắt đầu dọn dẹp và đồng bộ lại AI...")
    try:
        # Xóa dữ liệu bộ nhớ cũ
        db.delete_collection()
        print("Đã xóa bộ nhớ cũ.")
        
        # Khởi tạo lại kết nối mới
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings_model)
        
        # Gọi hàm đọc và nạp lại toàn bộ file PDF hiện có
        await asyncio.to_thread(process_pdfs, str(PDF_SRC_DIR))
        return {"message": "Đã làm mới bộ nhớ AI thành công!"}
    except Exception as e:
        print(f"❌ Lỗi Sync: {e}")
        return {"error": str(e)}

# ==========================================
# QUẢN LÝ KẾT NỐI ROBOT (SUBPROCESS)
# ==========================================
robot_process = None

class ConnectRequest(BaseModel):
    sn: str

@app.post("/api/robot/connect")
async def connect_robot(req: ConnectRequest):
    global robot_process
    
    sn = req.sn.strip()
    if not sn:
        return {"error": "Mã SN không được để trống"}
        
    try:
        # Nếu đang có robot chạy thì tắt đi
        if robot_process is not None:
            robot_process.terminate()
            robot_process = None
            
        # Ghi mã SN vào file config để robotchat.py đọc
        config_path = BASE_DIR / "robot_config.json"
        with open(config_path, "w") as f:
            json.dump({"SERIAL_NUMBER": sn}, f)
            
        # Kích hoạt robotchat.py chạy ngầm
        script_path = BASE_DIR / "robotchat.py"
        robot_process = subprocess.Popen(["python", str(script_path)])
        
        return {"message": f"Đã gửi lệnh kết nối tới Robot {sn}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/robot/disconnect")
async def disconnect_robot():
    global robot_process
    try:
        if robot_process is not None:
            robot_process.terminate()
            robot_process = None
        return {"message": "Đã ngắt kết nối Robot"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
