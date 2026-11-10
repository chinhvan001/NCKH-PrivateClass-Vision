import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_privateclass_vision/core/utils/firestore_parsers.dart';

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
    final data = doc.data() as Map<String, dynamic>? ?? {};

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
    String? id, String? classId, String? teacherId, String? classroomId,
    String? cameraId, String? className, String? room, String? date,
    String? start, String? end, int? size, int? presentStudent,
    double? avgAttentionScore, String? note, String? status,
    String? subject, String? period, String? sessionType,
  }) {
    return SessionModel(
      id: id ?? this.id, classId: classId ?? this.classId,
      teacherId: teacherId ?? this.teacherId,
      classroomId: classroomId ?? this.classroomId,
      cameraId: cameraId ?? this.cameraId,
      className: className ?? this.className, room: room ?? this.room,
      date: date ?? this.date, start: start ?? this.start,
      end: end ?? this.end, size: size ?? this.size,
      presentStudent: presentStudent ?? this.presentStudent,
      avgAttentionScore: avgAttentionScore ?? this.avgAttentionScore,
      note: note ?? this.note, status: status ?? this.status,
      subject: subject ?? this.subject, period: period ?? this.period,
      sessionType: sessionType ?? this.sessionType,
    );
  }


  /// Parse from Firestore `sessions` collection.
  /// Firestore schema: start_time/end_time = string "07:55",
  /// session_date = string "2026-11-09", room = string "302".
  factory SessionModel.fromFirestore(
    DocumentSnapshot doc, {
    String className = 'Lớp học',
    int classSize = 0,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    // ── session_date: "2026-11-09" → "09/11/2026" ──
    String dateStr = '';
    final rawDate = data['session_date'];
    if (rawDate is Timestamp) {
      final dt = rawDate.toDate();
      dateStr = '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    } else if (rawDate is String && rawDate.isNotEmpty) {
      if (rawDate.contains('-')) {
        final parts = rawDate.split('-');
        if (parts.length == 3) {
          dateStr = '${parts[2]}/${parts[1]}/${parts[0]}';
        } else {
          dateStr = rawDate;
        }
      } else {
        dateStr = rawDate;
      }
    }

    // ── start_time / end_time: string "07:55" hoặc Timestamp ──
    String startStr = '';
    String endStr = '';
    final rawStart = data['start_time'];
    final rawEnd = data['end_time'];
    if (rawStart is String) {
      startStr = rawStart;
    } else if (rawStart is Timestamp) {
      final dt = rawStart.toDate();
      startStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
      if (dateStr.isEmpty) {
        dateStr = '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      }
    }
    if (rawEnd is String) {
      endStr = rawEnd;
    } else if (rawEnd is Timestamp) {
      final dt = rawEnd.toDate();
      endStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    }

    // ── status ──
    String rawStatus = data['status']?.toString() ?? 'scheduled';
    String computedStatus;
    switch (rawStatus) {
      case 'running':
      case 'Đang diễn ra':
        computedStatus = 'Đang diễn ra';
        break;
      case 'completed':
      case 'Đã kết thúc':
        computedStatus = 'Đã kết thúc';
        break;
      case 'paused':
      case 'Tạm dừng':
        computedStatus = 'Tạm dừng';
        break;
      case 'scheduled':
      case 'Sắp diễn ra':
      default:
        computedStatus = 'Sắp diễn ra';
        break;
    }

    final String room = data['room']?.toString() ?? 'N/A';

    int studentCount = 0;
    int presentCountFromData = 0;
    final rawMonitored = data['monitored_students'] ?? data['mnoitored_student'] ?? data['monitored_student'];
    if (rawMonitored is Map) {
      final valid = rawMonitored.entries.where((e) => e.value is Map && FirestoreParsers.cleanId((e.value as Map)['student_id']) != null).toList();
      studentCount = valid.length;
      presentCountFromData = valid.where((e) => (e.value as Map)['is_present'] == true).length;
    } else {
      final List dyn = data['students'] is List ? data['students'] : [];
      final valid = dyn.where((s) => s is Map && (s['student_id']?.toString().trim().isNotEmpty == true) && s['student_id']?.toString() != 'null').toList();
      studentCount = valid.length;
      presentCountFromData = valid.where((s) => s is Map && s['is_present'] == true).length;
    }

    final int presentCount = (data['present_student'] as num?)?.toInt() ?? presentCountFromData;
    final double attentionScore = (data['avg_attention_score'] as num?)?.toDouble() ?? 0.0;
    final int finalSize = classSize > 0 ? classSize : (studentCount > 0 ? studentCount : presentCount);
    final int safePresentCount = presentCount > finalSize ? finalSize : presentCount;

    return SessionModel(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      teacherId: data['teacher_id']?.toString() ?? '',
      classroomId: room,
      cameraId: FirestoreParsers.string(data, ['camera_id']),
      className: className, room: room,
      date: dateStr, start: startStr, end: endStr,
      size: finalSize, presentStudent: safePresentCount,
      avgAttentionScore: attentionScore,
      note: data['note']?.toString() ?? '',
      status: computedStatus,
      subject: FirestoreParsers.string(data, ['subject']),
      period: FirestoreParsers.string(data, ['period']),
      sessionType: FirestoreParsers.string(data, ['session_type', 'sesion_type']),
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
    required this.id, required this.classId, required this.className,
    required this.classroomId, required this.roomName,
    required this.startTime, required this.endTime, required this.teacherId,
  });

  factory ScheduleItem.fromFirestore(
    DocumentSnapshot doc, {
    required String className, required String roomName,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};
    DateTime parseToDateTime(dynamic timeVal, dynamic dateVal) {
      if (timeVal is Timestamp) return timeVal.toDate();
      if (timeVal is String && timeVal.contains(':')) {
        final parts = timeVal.split(':');
        final hour = int.tryParse(parts[0]) ?? 0;
        final minute = parts.length > 1 ? (int.tryParse(parts[1]) ?? 0) : 0;
        DateTime baseDate = DateTime.now();
        if (dateVal is String && dateVal.contains('-')) {
          baseDate = DateTime.tryParse(dateVal) ?? DateTime.now();
        } else if (dateVal is Timestamp) {
          baseDate = dateVal.toDate();
        }
        return DateTime(baseDate.year, baseDate.month, baseDate.day, hour, minute);
      }
      return DateTime.now();
    }
    final rawDate = data['session_date'];
    final start = parseToDateTime(data['start_time'], rawDate);
    final end = parseToDateTime(data['end_time'], rawDate);
    return ScheduleItem(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      className: className,
      classroomId: data['room']?.toString() ?? '',
      roomName: roomName,
      startTime: start, endTime: end,
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

