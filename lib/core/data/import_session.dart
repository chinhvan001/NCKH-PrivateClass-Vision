import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

Future<void> addSessionForClass12A1() async {
  final FirebaseFirestore firestore = FirebaseFirestore.instance;

  try {
    // 1. Đọc document 'lop12a1' từ collection 'classes2' để lấy seat_map
    DocumentSnapshot classDoc = await firestore.collection('classes2').doc('lop12a1').get();

    if (!classDoc.exists) {
      debugPrint("Không tìm thấy lớp lop12a1 trong collection classes2!");
      return;
    }

    Map<String, dynamic> classData = classDoc.data() as Map<String, dynamic>;
    Map<String, dynamic> seatMap = classData['seat_map'] ?? {};

    if (seatMap.isEmpty) {
      debugPrint("Lớp lop12a1 không có dữ liệu seat_map!");
      return;
    }

    // 2. Xây dựng dữ liệu cho monitored_students dựa trên seat_map của lớp
    Map<String, dynamic> monitoredStudents = {};

    seatMap.forEach((seatId, seatValue) {
      Map<String, dynamic> seat = seatValue as Map<String, dynamic>;
      
      monitoredStudents[seatId] = {
        "student_id": seat['student_id'] ?? "null",
        "row": seat['row'] ?? 1,
        "column": seat['column'] ?? 1,
        "is_attention": false, // Mặc định là false
        "is_present": false,    // Mặc định có mặt (hoặc false tùy logic của bạn)
        "attention_score": 0.0, // Kiểu double mặc định là 0.0
        "note": "",            // Để trống
      };
    });

    // 3. Thiết lập thời gian cho buổi học (Ví dụ: Hôm nay, từ 7:00 đến 7:45)
    DateTime now = DateTime.now();
    DateTime startDate = DateTime(now.year, now.month, now.day, 7, 0);
    DateTime endDate = DateTime(now.year, now.month, now.day, 7, 45);

    Timestamp sessionDateTimestamp = Timestamp.fromDate(DateTime(now.year, now.month, now.day));
    Timestamp startTimeTimestamp = Timestamp.fromDate(startDate);
    Timestamp endTimeTimestamp = Timestamp.fromDate(endDate);

    // 4. Dữ liệu của session mới theo đúng yêu cầu
    Map<String, dynamic> sessionData = {
      "class_id": "lop12a1",
      "class_attention_score": 0.0,
      "subject": "Toán",
      "period": 1,
      "room": "302",
      "session_type": "morning", // hoặc 'morning' tùy theo định dạng của bạn
      "status": "scheduled",
      "teacher_id": "", // Để trống
      "camera_id": "",  // Để trống
      "note": "",       // Để trống
      "session_date": sessionDateTimestamp,
      "start_time": startTimeTimestamp,
      "end_time": endTimeTimestamp,
      "monitored_students": monitoredStudents,
      "created_at": Timestamp.now(),
      "updated_at": Timestamp.now(),
    };

    // 5. Thêm document mới vào collection 'sessions' (Firestore sẽ tự sinh ID ngẫu nhiên cho session)
    await firestore.collection('sessions').add(sessionData);

    debugPrint("Đã thêm thành công buổi học cho lớp 12A1 vào collection sessions với ${monitoredStudents.length} học sinh được giám sát!");
  } catch (e) {
    debugPrint("Lỗi khi thêm session: $e");
  }
}