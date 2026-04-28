import os
from google import genai
import sys

GEMINI_KEYS = [
    "AIzaSyDSJKtuTaRB_390yF9bFTi9jBUVzCglnEc",
    "AIzaSyB0A9ygmRFQeYRfObTqQVcvqePCikTUnFc",
    "AIzaSyCsl3vF35Xpc_yzt_RceQvQWU7X3WgIhUQ",
]

print("--- BẮT ĐẦU QUÉT HỆ THỐNG ---")
for i, key in enumerate(GEMINI_KEYS):
    print(f"\nKiểm tra Key #{i+1}: {key[:10]}...")
    client = genai.Client(api_key=key)
    
    try:
        print("  Các model khả dụng với Key này:")
        # Liệt kê tất cả model mà Key này được phép dùng
        models = client.models.list()
        found_models = []
        for m in models:
            name = m.name.replace("models/", "")
            found_models.append(name)
            print(f"    - {name}")
        
        # Thử gọi model đầu tiên tìm thấy để check Quota
        if found_models:
            target = "gemini-2.0-flash" if "gemini-2.0-flash" in found_models else found_models[0]
            print(f"  -> Đang thử gọi mẫu model '{target}'...", end="")
            res = client.models.generate_content(model=target, contents="Hi")
            print(" ✅ OK!")
    except Exception as e:
        err = str(e).lower()
        if "429" in err:
            print(" ❌ HẾT QUOTA (429). Key này ổn nhưng cần đợi reset.")
        elif "400" in err:
            print(" ❌ LỖI 400. Có thể do cấu hình API version.")
        else:
            print(f" ❌ LỖI KHÁC: {e}")

print("\n--- KẾT THÚC QUÉT ---")
