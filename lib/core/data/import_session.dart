import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

Future<void> addSessionsForClass12A1() async {
  final firestore = FirebaseFirestore.instance;
  final teacherId = FirebaseAuth.instance.currentUser?.uid;

  if (teacherId == null || teacherId.isEmpty) {
    debugPrint('Chưa đăng nhập, không có teacher_id!');
    return;
  }
    // 1. Đọc seat_map của lớp
    const classId = 'lop12a1';
    final classDoc = await firestore.collection('classes2').doc(classId).get();
    if (!classDoc.exists) {
      debugPrint('Không tìm thấy lớp $classId trong classes2!');
      return;
    }

    final classData = classDoc.data() ?? {};
    final rawSeatMap = classData['seat_map'] ?? classData['seatmap'];
    if (rawSeatMap is! Map || rawSeatMap.isEmpty) {
      debugPrint('Lớp $classId không có seat_map!');
      return;
    }

    // 2. Dựng monitored_students từ seat_map
    final Map<String, dynamic> monitoredStudents = {};
    rawSeatMap.forEach((seatId, seatValue) {
      final seat = Map<String, dynamic>.from(seatValue as Map);
      monitoredStudents[seatId.toString()] = {
        'student_id': seat['student_id'] ?? 'null',
        'row': seat['row'] ?? 1,
        'column': seat['column'] ?? 1,
        'is_attention': false,
        'is_present': false,
        'attention_score': 0.0,
        'note': '',
      };
    });

    // 3. Khung giờ 5 tiết: (giờ bắt đầu, phút bắt đầu)
    //    Mỗi tiết 45 phút; nghỉ 5 phút, riêng giữa tiết 3 và 4 nghỉ 15 phút.
    const periodStarts = [
      [7, 0], // tiết 1: 7:00 - 7:45
      [7, 50], // tiết 2: 7:50 - 8:35
      [8, 40], // tiết 3: 8:40 - 9:25
      [9, 40], // tiết 4: 9:40 - 10:25 (nghỉ 15p)
      [10, 30], // tiết 5: 10:30 - 11:15
    ];
    const periodMinutes = 45;

    final firstDay = DateTime(2026, 11, 2);
    const totalDays = 7; // 2/11 -> 8/11

    // 4. Ghi bằng batch (35 document, dưới giới hạn 500)
    final batch = firestore.batch();
    int count = 0;

    for (int d = 0; d < totalDays; d++) {
      final day = DateTime(firstDay.year, firstDay.month, firstDay.day + d);

      // DateTime.weekday: 1 = Thứ 2 ... 6 = Thứ 7, 7 = Chủ nhật
      final thu = day.weekday == DateTime.sunday ? 'CN' : '${day.weekday + 1}';

      for (int p = 0; p < periodStarts.length; p++) {
        final start = DateTime(
            day.year, day.month, day.day, periodStarts[p][0], periodStarts[p][1]);
        final end = start.add(const Duration(minutes: periodMinutes));

        // Tên document: gvtoan_tiet{N}_thu{M}_ngay{P}
        final docId = 'gvtoan_tiet${p + 1}_thu${thu}_ngay${day.day}';

        batch.set(firestore.collection('sessions').doc(docId), {
          'class_id': classId,
          'class_attention_score': 0.0,
          'subject': 'Toán',
          'period': p + 1,
          'room': '302',
          'session_type': 'morning',
          'status': 'scheduled',
          'teacher_id': teacherId,
          'camera_id': '',
          'note': '',
          'session_date': Timestamp.fromDate(day),
          'start_time': Timestamp.fromDate(start),
          'end_time': Timestamp.fromDate(end),
          'monitored_students': monitoredStudents,
          'created_at': Timestamp.now(),
          'updated_at': Timestamp.now(),
        });
        count++;
      }
    }

    await batch.commit();
    debugPrint('Đã thêm $count buổi học cho $classId (teacher: $teacherId).');
}