@echo off
title ALPHA MINI SYSTEM STARTUP
color 0B

echo ========================================================
echo        KHOI DONG HE THONG ALPHA MINI - AI RAG
echo ========================================================
echo.

echo 1. Kiem tra Moi truong ao (VENV)...
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [!] Chua co VENV. Dang tao moi truong ao cuc bo...
    python -m venv venv
    IF EXIST "chroma_db" (
        echo [!] Phat hien cai dat moi, dang don dep bo nho ChromaDB cu de tranh loi phien ban...
        rmdir /S /Q chroma_db
    )
)
echo [OK] Kich hoat moi truong ao...
call venv\Scripts\activate
echo [OK] Dang nang cap cong cu tai (pip) len ban moi nhat de tranh loi bien dich...
python -m pip install --upgrade pip setuptools wheel
echo.

echo 2. Dang kiem tra va cai dat thu vien (Neu chua co)...
echo (Vui long doi vai phut de tai du lieu neu la may moi)
pip install -r requirements.txt
echo.
echo [OK] Thu vien da san sang!
echo.

echo 3. Dang quet va nap du lieu PDF vao bo nho AI...
python ingest_pdf.py
echo.

echo 4. Dang mo giao dien dieu khien Web...
start web_view\index.html
echo [OK] Da gui lenh mo trinh duyet!
echo.

echo 5. Dang khoi dong May chu Trung Tam...
echo (Khong duoc tat cua so nay trong suot qua trinh chay)
echo --------------------------------------------------------
python server.py

pause
