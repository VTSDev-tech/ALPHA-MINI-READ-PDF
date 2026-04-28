import asyncio
import logging
import mini.mini_sdk as MiniSdk

# Bật log DEBUG để xem chi tiết SDK đang làm gì
logging.basicConfig(level=logging.DEBUG)
MiniSdk.set_log_level(logging.DEBUG)
MiniSdk.set_robot_type(MiniSdk.RobotType.EDU)

async def test_scan():
    print("\n🔍 Đang quét toàn bộ Robot Alpha Mini trong mạng nội bộ...")
    # Quét tất cả thiết bị trong 15 giây
    devices = await MiniSdk.get_device_list(timeout=15)
    
    if not devices:
        print("\n❌ KHÔNG TÌM THẤY BẤT KỲ ROBOT NÀO.")
        print("Gợi ý: Hãy thử khởi động lại WiFi hoặc tắt Firewall của máy tính.")
    else:
        print(f"\n✅ ĐÃ TÌM THẤY {len(devices)} THIẾT BỊ:")
        for dev in devices:
            print(f"---")
            print(f"Tên: {dev.name}")
            print(f"Địa chỉ: {dev.address}")
            print(f"ID: {dev.id}")
        
        print("\nSo sánh với Serial trong code của bạn: EAA007UBT10000339")

if __name__ == "__main__":
    asyncio.run(test_scan())
