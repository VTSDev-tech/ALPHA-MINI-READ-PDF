# Kế hoạch Triển khai: Alpha Mini + RAG Web Dashboard

Tuyệt vời! Chúng ta sẽ tích hợp giao diện màn hình TV (Web Dashboard) song song với hệ thống Robot thông qua kiến trúc Bất đồng bộ (Asyncio). Kế hoạch này giúp biến PC của bạn thành một Máy chủ Đa nhiệm hoàn hảo.

## 🏛 Kiến trúc Hệ thống

1.  **Lõi AI RAG (Thêm mới):** Sử dụng `LangChain` kết hợp cơ sở dữ liệu `ChromaDB` cục bộ để ăn 15 file PDF và trích xuất đoạn văn phù hợp cho câu hỏi.
2.  **Máy chủ Web & Socket (Thêm mới):** Dùng `FastAPI`, đây là framework Python hỗ trợ Asyncio nhanh nhất hiện nay. Mở một kênh Websocket để liên lạc trực tiếp (thời gian thực) giữa code Python và giao diện trên tivi.
3.  **Chatbot Loop (Giữ nguyên & Nâng cấp):** Thay vì chỉ bắt Robot nhép miệng, vòng lặp `robotchat.py` sẽ gửi thêm 1 gói dữ liệu (Chứa nội dung trang PDF) sang kênh Websocket để Tivi tự động phản ứng.

---

## 🛠 Các Phân Hệ (Modules) Cần Lập Trình

### 1. Phân hệ Giao diện Web (Tivi View)
*   **Thư mục chứa:** Tạo thư mục `d:\alphamini\web_view` chứa các file HTML tĩnh.
*   **Màn hình:** Một giao diện HTML rực rỡ, bo góc hiện đại. Có khung hình để hiển thị Ảnh trang PDF (hoặc đoạn tóm tắt tĩnh). Khi chưa có ai hỏi, màn hình sẽ chạy logo xoay vòng hoặc slide chờ. 
*   **Logic (JS):** Javascript dưới nền sẽ luôn lắng nghe kênh Websocket. Bất cứ khi nào nhận được tin nhắn từ AI "Lật trang số 3 file A", Giao diện lập tức phô bày hình ảnh trang số 3 lên giữa màn hình.

### 2. Phân hệ Máy chủ (FastAPI Server)
*   Sử dụng thư viện `fastapi`, `uvicorn`.
*   Vì trong `robotchat.py` của bạn vốn đã dùng thư viện `asyncio` để điều khiển Robot, ta sẽ cài cắm Web Server chạy chung luồng (Event Loop) với con Robot. Nghĩa là chúng nó hoạt động hòa quyện với nhau mà không lo bị ngắt quãng STT/TTS.

### 3. Phân hệ Xử lý RAG (Knowledge Base)
*   Tạo file `pdf_brain.py`.
*   Cài đặt thư viện `PyMuPDF` (đọc PDF sắc nét) và `chromadb` (lưu kết quả nội dung).
*   **Quá trình:**
    *   Hỏi: *"Giá sản phẩm A là bao nhiêu"*
    *   `pdf_brain.py` tìm trong DB Vector -> Thấy giá ở trang số 5 của file PDF `banggia.pdf`.
    *   Gửi trang 5 lên màn hình qua Websocket.
    *   Gửi lệnh cho Tivi render trang 5.
    *   Dùng AI tóm tắt: *"Dạ, dựa vào bảng giá trên tivi, sản phẩm A có giá 200k ạ"*.
    *   Gửi câu nói về Robot để đọc và cử động.

---

## 📅 Roadmap Thực thi
Để kiểm soát rủi ro, chúng ta sẽ code làm 2 đợt:

**👉 Đợt 1 (Xây Nền Giao Diện Trước):** Cài đặt FastAPI lên máy bạn. Thiết kế cái giao diện HTML. Gắn nó vào vòng lặp Robot hiện tại (chưa cần ráp PDF thật vội). Mỗi khi Robot trả lời câu hỏi bất kỳ, màn hình Tivi lập tức in siêu to câu trả lời hoặc một hình ảnh minh họa tự động. Bạn test xem Robot và Tivi có "Ăn khớp" với nhau không đã.

**👉 Đợt 2 (Bơm Thức Ăn PDF):** Nếu màn chiếu ngon rồi, mình sẽ viết công cụ RAG. Bắt đầu nhét 15 file PDF của bạn vào máy để cắt lát. Nối kết quả RAG vào luồng hỏi đáp, thay thế hoàn toàn bộ não chay hiện tại.
