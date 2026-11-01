import subprocess
import os

class LDPlayerService:
    @staticmethod
    def get_ld_path():
        # Đường dẫn chính xác đã tìm thấy trên máy của bạn
        path = r"D:\LDPlayer\LDPlayer9\dnconsole.exe"
        if os.path.exists(path):
            return path
        return None

    @staticmethod
    def launch_emulator(index=0):
        ld_path = LDPlayerService.get_ld_path()
        if not ld_path:
            raise FileNotFoundError("Không tìm thấy file dnconsole.exe của LDPlayer tại đường dẫn D:\\LDPlayer\\LDPlayer9\\dnconsole.exe!")
        
        # Lệnh chạy LDPlayer theo index (mở máy ảo index 0)
        command = [ld_path, "launch", "--index", str(index)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return {"success": True, "output": result.stdout}
        except subprocess.CalledProcessError as e:
            raise Exception(f"Lỗi khi khởi chạy LDPlayer: {e.stderr}")