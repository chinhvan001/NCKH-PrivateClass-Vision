import 'package:fake_cloud_firestore/fake_cloud_firestore.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_privateclass_vision/core/services/parent_service.dart';

/// Tiết như web admin ghi: session_date "YYYY-MM-DD", giờ "HH:MM", map monitored_students
Future<void> lesson(
  FakeFirebaseFirestore db,
  String id,
  String date,
  Map<String, dynamic> seat, {
  String start = '00:00',
  String end = '00:00',
}) {
  return db.collection('sessions').doc(id).set({
    'class_id': 'c1',
    'subject': 'Toán',
    'session_date': date,
    'start_time': start,
    'end_time': end,
    'period': 1,
    'status': 'completed',
    'monitored_students': {
      'S01': {'student_id': 'an', ...seat},
    },
  });
}

void main() {
  test('tiết chưa chấm điểm không bị tính thành 0%', () async {
    final db = FakeFirebaseFirestore();
    final now = DateTime.now();
    // 00:00 hôm nay: luôn đã kết thúc và nằm trong tháng này
    final today = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    await lesson(db, 'scored', today, {'is_present': true, 'attention_score': 100});
    await lesson(db, 'unscored', today, {'is_present': true, 'attention_score': null});

    final stats = await ParentService(db: db).getOverviewStats(
      studentId: 'an',
      classIds: ['c1'],
      period: 'Tháng này',
    );
    expect(stats.subjects.single.percent, 100);
  });

  test('thông báo vắng mang giờ của tiết web ("HH:MM" + session_date)', () async {
    final db = FakeFirebaseFirestore();
    await lesson(db, 'absent', '2026-11-16', {'is_present': false}, start: '07:00', end: '07:45');

    final notes = await ParentService(db: db).getNotificationsForStudent(studentId: 'an', classIds: ['c1']);
    expect(notes.single.startTime, DateTime(2026, 11, 16, 7));
    expect(notes.single.endTime, DateTime(2026, 11, 16, 7, 45));
    expect(notes.single.timestamp, DateTime(2026, 11, 16, 7, 45)); // "x phút trước" tính từ lúc tiết kết thúc
  });
}
