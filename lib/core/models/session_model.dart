import 'package:cloud_firestore/cloud_firestore.dart';

class ScheduleItem {
  final String id;
  final String classId;
  final String className;
  final String classroomId;
  final String roomName;
  final DateTime startTime;
  final DateTime endTime;
  final String teacherId;

  ScheduleItem({
    required this.id,
    required this.classId,
    required this.className,
    required this.classroomId,
    required this.roomName,
    required this.startTime,
    required this.endTime,
    required this.teacherId,
  });

  factory ScheduleItem.fromFirestore(
    DocumentSnapshot doc, {
    required String className,
    required String roomName,
  }) {
    final data = doc.data() as Map<String, dynamic>;

    final start = data['start_time'] is Timestamp
        ? (data['start_time'] as Timestamp).toDate()
        : DateTime.now();
    final end = data['end_time'] is Timestamp
        ? (data['end_time'] as Timestamp).toDate()
        : DateTime.now();

    return ScheduleItem(
      id: doc.id,
      classId: data['class_id'] ?? '',
      className: className,
      classroomId: data['classroom_id'] ?? '',
      roomName: roomName,
      startTime: start,
      endTime: end,
      teacherId: data['teacher_id'] ?? '',
    );
  }

  String get status {
    final now = DateTime.now();
    if (now.isAfter(endTime)) return 'Đã kết thúc';
    if (now.isBefore(startTime)) return 'Sắp diễn ra';
    return 'Đang diễn ra';
  }
}