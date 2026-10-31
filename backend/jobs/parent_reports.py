"""Job tạo báo cáo phụ huynh (UC03) sau mỗi tiết học, và tự kết thúc tiết giáo viên quên bấm Kết thúc
(quá 30 phút sau giờ kết thúc). Chạy từ thư mục backend/:

    python -m jobs.parent_reports               # 1 lượt; đặt lịch 10 phút/lần (Task Scheduler, cron)
    python -m jobs.parent_reports --every 600   # tự lặp 10 phút/lần
    python -m jobs.parent_reports --session ID  # tạo lại báo cáo của một tiết, không chờ camera AI chốt

Cần cùng cấu hình Firebase với backend (serviceAccountKey.json hoặc FIREBASE_SERVICE_ACCOUNT trong .env).
"""

import argparse
import time

from services import monitoring_service, report_service


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tạo báo cáo phụ huynh cho các tiết đã kết thúc.")
    parser.add_argument("--every", type=int, default=0, metavar="GIÂY", help="lặp lại sau mỗi chừng này giây")
    parser.add_argument("--session", metavar="ID", help="chỉ tạo (lại) báo cáo của tiết này")
    args = parser.parse_args(argv)

    if args.session:
        count = report_service.build_session_reports(args.session, force=True)
        print(f"Tiết {args.session}: " + ("chưa kết thúc." if count is None else f"{count} báo cáo."))
        return
    while True:
        closed = monitoring_service.close_forgotten_sessions()
        if closed:
            print(f"Đã tự kết thúc {len(closed)} tiết quên bấm Kết thúc: {', '.join(closed)}.", flush=True)
        built = report_service.build_pending_reports()
        print(f"Đã tạo báo cáo cho {len(built)} tiết ({sum(built.values())} học sinh).", flush=True)
        if args.every <= 0:
            return
        time.sleep(args.every)


if __name__ == "__main__":
    main()
