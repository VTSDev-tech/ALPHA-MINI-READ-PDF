// Cập nhật Đồng hồ liên tục
function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    document.getElementById('clock').textContent = `${hours}:${minutes}`;
}
setInterval(updateClock, 1000);
updateClock();

// Đối tượng DOM
const idleState = document.getElementById('idle-state');
const docViewer = document.getElementById('document-viewer');
const docName = document.getElementById('doc-name');
const docPage = document.getElementById('doc-page');
const insightList = document.getElementById('insight-list');
const pdfImg = document.getElementById('pdf-page-img');
const docCard = document.querySelector('.doc-card');

// Hàm hiển thị trang tài liệu
window.showDocumentMode = function(fileName, pageStr, imageSrc, insights) {
    idleState.classList.add('hidden');
    docViewer.classList.remove('hidden');
    docCard.classList.add('active');
    docPage.classList.add('active');
    
    docName.textContent = fileName;
    docPage.textContent = pageStr;
    
    insightList.innerHTML = '';
    if (insights && insights.length > 0) {
        insights.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            insightList.appendChild(li);
        });
    } else {
        insightList.innerHTML = '<li class="empty-state"><p>Không tìm thấy ý chính</p></li>';
    }

    if (imageSrc) {
        pdfImg.src = imageSrc;
        pdfImg.classList.remove('hidden');
    }
};

window.showIdleMode = function() {
    idleState.classList.remove('hidden');
    docViewer.classList.add('hidden');
    docCard.classList.remove('active');
    docPage.classList.remove('active');
    
    docName.textContent = "Chưa có tài liệu";
    docPage.textContent = "--";
    insightList.innerHTML = '<li class="empty-state"><i class="ph-duotone ph-chat-teardrop-dots"></i><p>Hãy hỏi Alpha Mini để gọi tài liệu xuất hiện trên màn hình...</p></li>';
};

// ==========================================
// KẾT NỐI MÁY CHỦ THỜI GIAN THỰC (WEBSOCKET)
// ==========================================
function connectWebSocket() {
    const host = window.location.hostname || "localhost";
    const ws = new WebSocket(`ws://${host}:8888/ws`); 

    ws.onopen = function() {
        console.log("🟢 Đã kết nối với Tổng Đài Điều Khiển (FastAPI)");
    };

    ws.onmessage = function(event) {
        console.log("⚡ Nhận Lệnh Bắn Tới: ", event.data);
        try {
            const data = JSON.parse(event.data);
            if (data.type === "document") {
                const host = window.location.hostname || "localhost";
                const fullImageUrl = data.image_url ? `http://${host}:8888${data.image_url}` : "";
                showDocumentMode(data.file_name, data.page, fullImageUrl, data.insights);
            } else if (data.type === "idle") {
                showIdleMode();
            }
        } catch (e) {
            console.error("Lỗi phân tích lệnh", e);
        }
    };

    ws.onclose = function() {
        console.warn("🔴 Đứt kết nối với Máy Chủ Của Robot. Cố gắn nối lại sau 3 giây...");
        setTimeout(connectWebSocket, 3000);
    };
}

// Bật kết nối
connectWebSocket();

// ==========================================
// TẢI LÊN FILE PDF MỚI TỪ DASHBOARD
// ==========================================
window.handleFileUpload = async function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const statusDiv = document.getElementById('upload-status');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> Đang tải và AI xử lý...';
    statusDiv.style.color = "var(--primary-blue)";
    statusDiv.style.backgroundColor = "var(--primary-glow)";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const host = window.location.hostname || "localhost";
        const response = await fetch(`http://${host}:8888/api/upload`, {
            method: "POST",
            body: formData
        });
        const result = await response.json();
        
        if (response.ok && !result.error) {
            statusDiv.innerHTML = `<i class="ph-bold ph-check-circle"></i> Đã xong: ${file.name}`;
            statusDiv.style.color = "#10B981";
            statusDiv.style.backgroundColor = "#D1FAE5";
        } else {
            statusDiv.innerHTML = `<i class="ph-bold ph-warning"></i> Lỗi: ${result.error || "Tải lên thất bại"}`;
            statusDiv.style.color = "#EF4444";
            statusDiv.style.backgroundColor = "#FEE2E2";
        }
    } catch (e) {
        statusDiv.innerHTML = `<i class="ph-bold ph-warning"></i> Lỗi kết nối!`;
        statusDiv.style.color = "#EF4444";
        statusDiv.style.backgroundColor = "#FEE2E2";
    }
    
    // Reset file input để có thể up lại cùng 1 file
    event.target.value = '';
    
    // Ẩn thông báo sau 5 giây
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
};

// ==========================================
// ĐỒNG BỘ LẠI DỮ LIỆU AI
// ==========================================
window.syncAIData = async function() {
    const statusDiv = document.getElementById('upload-status');
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> Đang tẩy não và học lại tài liệu...';
    statusDiv.style.color = "var(--primary-blue)";
    statusDiv.style.backgroundColor = "var(--primary-glow)";
    
    try {
        const host = window.location.hostname || "localhost";
        const response = await fetch(`http://${host}:8888/api/sync`, { method: "POST" });
        const result = await response.json();
        
        if (response.ok && !result.error) {
            statusDiv.innerHTML = `<i class="ph-bold ph-check-circle"></i> ${result.message}`;
            statusDiv.style.color = "#10B981";
            statusDiv.style.backgroundColor = "#D1FAE5";
        } else {
            statusDiv.innerHTML = `<i class="ph-bold ph-warning"></i> Lỗi: ${result.error}`;
            statusDiv.style.color = "#EF4444";
            statusDiv.style.backgroundColor = "#FEE2E2";
        }
    } catch (e) {
        statusDiv.innerHTML = `<i class="ph-bold ph-warning"></i> Lỗi mất kết nối tới Server!`;
        statusDiv.style.color = "#EF4444";
        statusDiv.style.backgroundColor = "#FEE2E2";
    }
    
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
};

// ==========================================
// KẾT NỐI ROBOT TỪ WEB
// ==========================================
let isRobotConnected = false;

window.toggleRobotConnection = async function() {
    const inputField = document.getElementById('robot-sn-input');
    const btnConnect = document.getElementById('btn-connect-robot');
    const statusText = document.getElementById('robot-status-text');
    const statusDot = document.getElementById('robot-status-dot');
    const host = window.location.hostname || "localhost";

    if (!isRobotConnected) {
        const sn = inputField.value.trim();
        if (!sn) {
            alert("Vui lòng nhập mã SN của Robot (VD: EAA...)");
            return;
        }

        btnConnect.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> Đang...';
        try {
            const response = await fetch(`http://${host}:8888/api/robot/connect`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sn: sn })
            });
            const result = await response.json();

            if (response.ok && !result.error) {
                isRobotConnected = true;
                inputField.disabled = true;
                inputField.style.opacity = "0.6";
                btnConnect.style.background = "#EF4444"; // Đỏ
                btnConnect.innerHTML = '<i class="ph-bold ph-power"></i> Ngắt';
                statusDot.style.background = "#10B981"; // Xanh lá
                statusDot.style.boxShadow = "0 0 8px rgba(16,185,129,0.5)";
                statusText.textContent = `Đang điều khiển: ${sn}`;
            } else {
                alert("Lỗi: " + (result.error || "Không thể kết nối"));
                btnConnect.innerHTML = '<i class="ph-bold ph-plugs"></i> Kết Nối';
            }
        } catch (e) {
            alert("Không thể kết nối đến Máy chủ (Server đang tắt?)");
            btnConnect.innerHTML = '<i class="ph-bold ph-plugs"></i> Kết Nối';
        }
    } else {
        // Ngắt kết nối
        btnConnect.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> Đang...';
        try {
            await fetch(`http://${host}:8888/api/robot/disconnect`, { method: "POST" });
        } catch (e) { console.error(e); }

        isRobotConnected = false;
        inputField.disabled = false;
        inputField.style.opacity = "1";
        inputField.value = "";
        btnConnect.style.background = "var(--primary-blue)";
        btnConnect.innerHTML = '<i class="ph-bold ph-plugs"></i> Kết Nối';
        statusDot.style.background = "#EF4444"; // Đỏ
        statusDot.style.boxShadow = "0 0 8px rgba(239,68,68,0.5)";
        statusText.textContent = "Chưa kết nối Robot";
    }
};
