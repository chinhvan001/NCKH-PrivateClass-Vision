import 'package:cloud_firestore/cloud_firestore.dart';

/// Một phiên học lấy từ collection `sessions`.
/// Tên lớp lấy từ `classes2/{class_id}.class_name` (do màn hình truyền vào).
class ScheduleItem {
  final String id;
  final String classId;
  final String className;
  final String cameraId;
  final String roomName;
  final String subject;
  final int period;
  final DateTime startTime;
  final DateTime endTime;
  final String teacherId;

  /// Số học sinh trong phiên (đếm từ `monitored_students`).
  final int studentCount;

  ScheduleItem({
    required this.id,
    required this.classId,
    required this.className,
    required this.cameraId,
    required this.roomName,
    required this.startTime,
    required this.endTime,
    required this.teacherId,
    this.subject = '',
    this.period = 0,
    this.studentCount = 0,
  });

  /// Tương thích code cũ còn dùng `classroomId` (nay là camera của phòng).
  String get classroomId => cameraId;

  factory ScheduleItem.fromFirestore(
    DocumentSnapshot doc, {
    required String className,
    String? roomName,
  }) {
    final data = doc.data() as Map<String, dynamic>;

    final start = data['start_time'] is Timestamp
        ? (data['start_time'] as Timestamp).toDate()
        : DateTime.now();
    final end = data['end_time'] is Timestamp
        ? (data['end_time'] as Timestamp).toDate()
        : DateTime.now();

    final room = (data['room'] ?? roomName ?? '').toString();

    return ScheduleItem(
      id: doc.id,
      classId: (data['class_id'] ?? '').toString(),
      className: className,
      cameraId: (data['camera_id'] ?? '').toString(),
      roomName: room.isEmpty ? 'Chưa cập nhật' : room,
      subject: (data['subject'] ?? '').toString(),
      period: data['period'] is num ? (data['period'] as num).toInt() : 0,
      startTime: start,
      endTime: end,
      teacherId: (data['teacher_id'] ?? '').toString(),
      studentCount: _countStudents(data['monitored_students']),
    );
  }

  static int _countStudents(dynamic raw) {
    if (raw is! Map) return 0;
    var n = 0;
    for (final v in raw.values) {
      if (v is! Map) continue;
      final id = v['student_id'];
      if (id is String && id.isNotEmpty && id != 'null') n++;
    }
    return n;
  }

  String get status {
    final now = DateTime.now();
    if (now.isAfter(endTime)) return 'Đã kết thúc';
    if (now.isBefore(startTime)) return 'Sắp diễn ra';
    return 'Đang diễn ra';
  }
}
