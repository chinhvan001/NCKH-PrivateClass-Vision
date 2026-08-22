import locale
locale.setlocale(locale.LC_ALL, 'C')

import cv2
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Không mở được camera — kiểm tra lại CAMERA_SOURCE hoặc quyền truy cập camera.")
else:
    ret, frame = cap.read()
    print("Camera OK, đọc được frame:", ret)
cap.release()