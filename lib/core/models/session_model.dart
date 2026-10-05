// File: lib/core/models/session_model.dart

import 'package:cloud_firestore/cloud_firestore.dart';

class SessionModel {
  final String id;
  final String classId;
  final String teacherId;
  final String classroomId;
  final String className;
  final String room;
  final String date;
  final String start;
  final String end;
  final int size;
  final int presentStudent;
  final double avgAttentionScore;
  final String note;
  final String status;

  SessionModel({
    required this.id,
    required this.classId,
    this.teacherId = '',
    this.classroomId = '',
    required this.className,
    required this.room,
    required this.date,
    required this.start,
    required this.end,
    required this.size,
    this.presentStudent = 0,
    this.avgAttentionScore = 0.0,
    this.note = '',
    required this.status,
  });

  factory SessionModel.fromFirestore(
    DocumentSnapshot doc, {
    String className = 'Lớp học',
    int classSize = 0,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    DateTime parseDateTime(dynamic val) {
      if (val is Timestamp) {
        return val.toDate();
      } else if (val is String) {
        return DateTime.tryParse(val) ?? DateTime.now();
      } else if (val is int) {
        return DateTime.fromMillisecondsSinceEpoch(val);
      }
      return DateTime.now();
    }

    final DateTime now = DateTime.now();
    final DateTime startDt = data['start_time'] != null
        ? parseDateTime(data['start_time'])
        : now;
    final DateTime endDt = data['end_time'] != null
        ? parseDateTime(data['end_time'])
        : startDt.add(const Duration(hours: 1));

    final String dateStr =
        '${startDt.day.toString().padLeft(2, '0')}/${startDt.month.toString().padLeft(2, '0')}/${startDt.year}';
    final String startStr =
        '${startDt.hour.toString().padLeft(2, '0')}:${startDt.minute.toString().padLeft(2, '0')}';
    final String endStr =
        '${endDt.hour.toString().padLeft(2, '0')}:${endDt.minute.toString().padLeft(2, '0')}';

    String computedStatus;
    if (now.isBefore(startDt)) {
      computedStatus = 'Sắp diễn ra';
    } else if (now.isAfter(endDt)) {
      computedStatus = 'Đã kết thúc';
    } else {
      computedStatus = 'Đang diễn ra';
    }

    // Lấy mảng students nếu có
    final List dynamicStudents = data['students'] is List
        ? data['students']
        : [];
    final int presentCountFromList = dynamicStudents
        .where((s) => s is Map && (s['is_present'] == true))
        .length;

    final int presentCount =
        (data['present_student'] as num?)?.toInt() ??
        (dynamicStudents.isNotEmpty ? presentCountFromList : 0);

    final double attentionScore =
        (data['avg_attention_score'] as num?)?.toDouble() ?? 0.0;

    return SessionModel(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      teacherId: data['teacher_id']?.toString() ?? '',
      classroomId: data['classroom_id']?.toString() ?? '',
      className: className,
      room:
          (data['classroom_id'] != null &&
              data['classroom_id'].toString().isNotEmpty)
          ? data['classroom_id'].toString()
          : 'N/A',
      date: dateStr,
      start: startStr,
      end: endStr,
      size: classSize > 0
          ? classSize
          : (dynamicStudents.isNotEmpty
                ? dynamicStudents.length
                : presentCount),
      presentStudent: presentCount,
      avgAttentionScore: attentionScore,
      note: data['note']?.toString() ?? '',
      status: computedStatus,
    );
  }
}

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
    final data = doc.data() as Map<String, dynamic>? ?? {};

    final start = data['start_time'] is Timestamp
        ? (data['start_time'] as Timestamp).toDate()
        : DateTime.now();
    final end = data['end_time'] is Timestamp
        ? (data['end_time'] as Timestamp).toDate()
        : DateTime.now();

    return ScheduleItem(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      className: className,
      classroomId: data['classroom_id']?.toString() ?? '',
      roomName: roomName,
      startTime: start,
      endTime: end,
      teacherId: data['teacher_id']?.toString() ?? '',
    );
  }

  String get status {
    final now = DateTime.now();
    if (now.isAfter(endTime)) return 'Đã kết thúc';
    if (now.isBefore(startTime)) return 'Sắp diễn ra';
    return 'Đang diễn ra';
  }
}
