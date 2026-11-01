import 'package:cloud_firestore/cloud_firestore.dart';

import '../utils/firestore_parsers.dart';

class SessionModel {
  final String id;
  final String classId;
  final String teacherId;
  final String classroomId;
  final String cameraId;
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
  final String subject;
  final String period;
  final String sessionType;

  SessionModel({
    required this.id,
    required this.classId,
    this.teacherId = '',
    this.classroomId = '',
    this.cameraId = '',
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
    this.subject = '',
    this.period = '',
    this.sessionType = '',
  });

  SessionModel copyWith({
    String? id,
    String? classId,
    String? teacherId,
    String? classroomId,
    String? cameraId,
    String? className,
    String? room,
    String? date,
    String? start,
    String? end,
    int? size,
    int? presentStudent,
    double? avgAttentionScore,
    String? note,
    String? status,
    String? subject,
    String? period,
    String? sessionType,
  }) {
    return SessionModel(
      id: id ?? this.id,
      classId: classId ?? this.classId,
      teacherId: teacherId ?? this.teacherId,
      classroomId: classroomId ?? this.classroomId,
      cameraId: cameraId ?? this.cameraId,
      className: className ?? this.className,
      room: room ?? this.room,
      date: date ?? this.date,
      start: start ?? this.start,
      end: end ?? this.end,
      size: size ?? this.size,
      presentStudent: presentStudent ?? this.presentStudent,
      avgAttentionScore: avgAttentionScore ?? this.avgAttentionScore,
      note: note ?? this.note,
      status: status ?? this.status,
      subject: subject ?? this.subject,
      period: period ?? this.period,
      sessionType: sessionType ?? this.sessionType,
    );
  }

  /// Parse from collection `session` (or `monitoring_sessions` fallback).
  factory SessionModel.fromFirestore(
    DocumentSnapshot doc, {
    String className = 'Lớp học',
    int classSize = 0,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    DateTime parseDateTime(dynamic val) {
      if (val is Timestamp) return val.toDate();
      if (val is String) return DateTime.tryParse(val) ?? DateTime.now();
      if (val is int) return DateTime.fromMillisecondsSinceEpoch(val);
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

    final dynamic rawStudents = data['monitored_students'] ??
        data['mnoitored_student'] ??
        data['monitored_student'] ??
        data['students'];

    int studentCount = 0;
    int presentCountFromData = 0;

    if (rawStudents is Map) {
      final validEntries = rawStudents.values.where((s) {
        if (s is! Map) return false;
        final studentId = FirestoreParsers.cleanId(s['student_id']);
        return studentId != null && studentId.isNotEmpty;
      }).toList();

      studentCount = validEntries.length;
      presentCountFromData = validEntries
          .where((s) => (s as Map)['is_present'] == true)
          .length;
    } else if (rawStudents is List) {
      final validStudents = rawStudents.where((s) {
        if (s is! Map) return false;
        final studentId = FirestoreParsers.cleanId(s['student_id']);
        return studentId != null && studentId.isNotEmpty;
      }).toList();

      studentCount = validStudents.length;
      presentCountFromData = validStudents
          .where((s) => (s as Map)['is_present'] == true)
          .length;
    }

    // Use studentCount and presentCountFromData to avoid unused warnings
    if (studentCount < 0) studentCount = 0;
    if (presentCountFromData < 0) presentCountFromData = 0;
      computedStatus = 'Đã kết thúc';
    } else {
      computedStatus = 'Đang diễn ra';
    }

    // ── Parse student count from Map or List ─────────────────────
    int studentCount = 0;
    int presentCountFromData = 0;

    final rawMonitored =
        data['mnoitored_students'] ?? data['monitored_students'];
    if (rawMonitored is Map) {
      final validEntries = rawMonitored.entries.where((e) {
        if (e.value is! Map) return false;
        final sid = FirestoreParsers.cleanId((e.value as Map)['student_id']);
        return sid != null;
      }).toList();
      studentCount = validEntries.length;
      presentCountFromData = validEntries
          .where((e) => (e.value as Map)['is_present'] == true)
          .length;
    } else {
      final List dynamicStudents = data['students'] is List
          ? data['students']
          : [];
      final validStudents = dynamicStudents
          .where(
            (s) =>
                s is Map &&
                (s['student_id']?.toString().trim().isNotEmpty == true) &&
                s['student_id']?.toString() != 'null',
          )
          .toList();
      studentCount = validStudents.length;
      presentCountFromData = validStudents
          .where((s) => s is Map && s['is_present'] == true)
          .length;
    }

    final int presentCount =
        (data['present_student'] as num?)?.toInt() ?? presentCountFromData;
    final double attentionScore =
        (data['avg_attention_score'] as num?)?.toDouble() ?? 0.0;
    final int finalSize = classSize > 0
        ? classSize
        : (studentCount > 0 ? studentCount : presentCount);
    final int safePresentCount = presentCount > finalSize
        ? finalSize
        : presentCount;

    return SessionModel(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      teacherId: data['teacher_id']?.toString() ?? '',
      classroomId: data['classroom_id']?.toString() ?? '',
      cameraId: FirestoreParsers.string(data, ['camera_id']),
      className: className,
      room: FirestoreParsers.string(data, ['classroom_id', 'camera_id'], 'N/A'),
      date: dateStr,
      start: startStr,
      end: endStr,
      size: finalSize,
      presentStudent: safePresentCount,
      avgAttentionScore: attentionScore,
      note: data['note']?.toString() ?? '',
      status: computedStatus,
      subject: FirestoreParsers.string(data, ['subject']),
      period: FirestoreParsers.string(data, ['period']),
      sessionType: FirestoreParsers.string(data, [
        'sesion_type',
        'session_type',
      ]),
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
