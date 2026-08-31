"""
logging_config.py -- Cau hinh logging tap trung cho toan bo camera-ai/

Goi setup_logging() DUY NHAT MOT LAN o dau moi entry point script (vi du
camera_test.py, detection_test.py, hoac main.py sau nay khi ghep pipeline
day du) truoc khi dung bat ky module nao khac.

Cac module con (capture/, detection/, engagement/...) khong can va KHONG NEN
tu goi logging.basicConfig() rieng -- chi can:

    logger = logging.getLogger("camera_ai.<ten_module>")

Vi tat ca logger con deu la con chau cua logger goc "camera_ai" trong cay
logging cua Python (phan cap theo dau cham), chung se tu dong ke thua handler
va level da cau hinh o day, khong can cau hinh lai tung noi.
"""

import logging
import logging.handlers
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Thu muc logs/ nam o goc camera-ai/ (ngang hang voi src/), khong phai ben
# trong src/ -- vi day la du lieu runtime (log file), khong phai code.
DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "camera-ai.log"

LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(
    level: str = None,
    log_file: Path = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
    console: bool = True,
) -> None:
    """Cau hinh logging cho toan bo camera-ai.

    An toan khi goi nhieu lan tu nhieu noi khac nhau -- chi cau hinh that su o
    lan goi dau tien, cac lan sau bi bo qua. Dieu nay tranh truong hop mot
    entry point vo tinh goi ham nay nhieu lan (vi du qua import chong cheo)
    gay nhan doi handler, dan den moi dong log bi in/ghi lap nhieu lan.

    Tham so:
        level: muc log toi thieu (DEBUG/INFO/WARNING/ERROR/CRITICAL). Neu
            None, doc tu bien moi truong LOG_LEVEL trong .env, mac dinh INFO
            neu .env cung khong co.
        log_file: duong dan file log. Neu None, dung logs/camera-ai.log o thu
            muc goc camera-ai/ (tu dong tao thu muc neu chua ton tai).
        max_bytes / backup_count: file log se TU DONG XOAY VONG (rotate) khi
            dat toi max_bytes, giu lai backup_count file cu (camera-ai.log.1,
            .log.2, ...). Bat buoc phai co co che nay vi tien trinh du kien
            chay lien tuc nhieu ngay/tuan tren may tinh truong -- neu khong
            xoay vong, file log se phinh to khong gioi han.
        console: co dong thoi in log ra terminal hay khong (mac dinh co). Dat
            False khi chay hoan toan o che do nen (background service), chi
            can ghi file.
    """
    global _configured
    if _configured:
        logging.getLogger("camera_ai").debug(
            "setup_logging() da duoc goi truoc do trong tien trinh nay, bo qua."
        )
        return

    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_log_file = Path(log_file) if log_file else DEFAULT_LOG_FILE
    resolved_log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Cau hinh o logger "camera_ai" (khong phai root logger tuyet doi cua
    # Python) -- moi logger con dang dung ("camera_ai.capture",
    # "camera_ai.detection"...) se tu ke thua qua co che propagate mac dinh.
    # propagate=False o day de chan khong cho log day tiep len root logger
    # cua Python, tranh in trung lap neu code khac (vi du mot thu vien ben
    # thu ba) co cau hinh root logger rieng.
    app_logger = logging.getLogger("camera_ai")
    app_logger.setLevel(resolved_level)
    app_logger.propagate = False

    file_handler = logging.handlers.RotatingFileHandler(
        resolved_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

    _configured = True
    app_logger.info(
        "Da cau hinh logging: level=%s, file=%s (rotate %d bytes x %d ban sao)",
        resolved_level, resolved_log_file, max_bytes, backup_count,
    )


def reset_logging_for_test() -> None:
    """Chi dung trong unit test: go het handler va reset trang thai
    _configured, cho phep goi lai setup_logging() nhu moi khoi dong tien
    trinh. KHONG goi ham nay trong code chay that."""
    global _configured
    app_logger = logging.getLogger("camera_ai")
    for handler in list(app_logger.handlers):
        app_logger.removeHandler(handler)
        handler.close()
    _configured = False