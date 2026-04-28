import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# ==========================================
# CẤU HÌNH LOCAL CHROMA
# ==========================================
load_dotenv()
CHROMA_PATH = "chroma_db"

def process_pdfs(path="Tai_lieu_PDF"):
    # print("🧹 Đang dọn dẹp dữ liệu trên Cloud...")
    # collection.delete_many({})

    if os.path.isfile(path):
        pdf_files = [path]
    else:
        pdf_files = glob.glob(f"{path}/*.pdf")
        
    if not pdf_files:
        print(f"❌ Không tìm thấy file tại '{path}'")
        return
        
    print(f"🔍 Đang nạp {len(pdf_files)} file vào Chroma DB...")
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings_model)

    for pdf_path in pdf_files:
        print(f"⏳ Đang nạp: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        chunks = text_splitter.split_documents(pages)

        for chunk in chunks:
            chunk.metadata["source"] = os.path.basename(pdf_path)
            
        db.add_documents(chunks)
            
        print(f" ✅ Hoàn tất lưu file vào Chroma: {pdf_path}")
    print("🎉 TẤT CẢ TÀI LIỆU ĐÃ LƯU OFFLINE THÀNH CÔNG!")

if __name__ == "__main__":
    os.makedirs("Tai_lieu_PDF", exist_ok=True)
    process_pdfs()
