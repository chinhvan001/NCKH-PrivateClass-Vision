import subprocess
import os
import time

class StreamAutomationService:
    LD_PATH = r"D:\LDPlayer\LDPlayer9\dnconsole.exe"
    MEDIAMTX_DIR = r"D:\Tools\mediamtx_v1.21.0_windows_amd64"
    FFMPEG_PATH = r"D:\Tools\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"

    @staticmethod
    def kill_existing_processes():
        # Dọn dẹp sạch sẽ các tiến trình ffmpeg cũ để tránh xung đột 'Broken pipe'
        try:
            subprocess.run(["taskkill", "/f", "/im", "ffmpeg.exe"], capture_output=True)
        except Exception:
            pass

    @staticmethod
    def start_mediamtx():
        mediamtx_exe = os.path.join(StreamAutomationService.MEDIAMTX_DIR, "mediamtx.exe")
        if os.path.exists(mediamtx_exe):
            res = subprocess.run('tasklist /fi "imagename eq mediamtx.exe"', capture_output=True, text=True, shell=True)
            if "mediamtx.exe" not in res.stdout:
                ps_command = f'powershell -NoExit -Command "cd \'{StreamAutomationService.MEDIAMTX_DIR}\'; ./mediamtx.exe"'
                subprocess.Popen(ps_command, shell=True)
                print("[MediaMTX] Đã mở cửa sổ PowerShell riêng cho MediaMTX.")
            else:
                print("[MediaMTX] Server đã chạy sẵn từ trước.")

    @staticmethod
    def start_ffmpeg_stream(stream_path="camera-p201a"):

        StreamAutomationService.kill_existing_processes()
        time.sleep(1)

        rtsp_url = f"rtsp://localhost:8554/{stream_path}"

        ffmpeg_inner_cmd = (
            f'"{StreamAutomationService.FFMPEG_PATH}" -hide_banner -loglevel error '
            f'-fflags nobuffer -flags low_delay '
            f'-f gdigrab -framerate 30 -draw_mouse 0 -i title="LDPlayer" '
            f'-vf "crop=560:340:35:130,scale=640:388" '
            f'-vcodec libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency -pkt_size 1400 '
            f'-rtsp_transport tcp '
            f'-f rtsp {rtsp_url}'
        )
        
        ps_command = f'powershell -NoExit -Command "{ffmpeg_inner_cmd}"'
        subprocess.Popen(ps_command, shell=True)
        print(f"[FFmpeg] Đã khởi chạy luồng cắt khung hình chuẩn cho: {stream_path}")

    @staticmethod
    def launch_all_system(index=0, stream_path="camera-p201a"):
        if not os.path.exists(StreamAutomationService.LD_PATH):
            raise FileNotFoundError("Không tìm thấy file LDPlayer dnconsole.exe")

        subprocess.run([StreamAutomationService.LD_PATH, "launch", "--index", str(index)], check=True)

        StreamAutomationService.start_mediamtx()

        print(f"[System] Đang chờ hệ thống ổn định cho {stream_path}...")
        time.sleep(5)

        StreamAutomationService.start_ffmpeg_stream(stream_path)

        return {
            "success": True, 
            "message": f"Đã khởi động hệ thống và luồng cho {stream_path} thành công!"
        }