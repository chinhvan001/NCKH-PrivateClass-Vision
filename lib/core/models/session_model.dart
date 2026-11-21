import 'package:cloud_firestore/cloud_firestore.dart';

/// Đọc ngày/giờ từ Firestore theo nhiều định dạng khác nhau.
/// Không bao giờ trả về "bây giờ" khi dữ liệu không đọc được (trả về null).
class SessionTimeParser {
  /// Timestamp, DateTime, số (ms hoặc giây), chuỗi ISO, chuỗi dd/MM/yyyy [HH:mm].
  static DateTime? dateTime(dynamic v) {
    if (v == null) return null;
    if (v is Timestamp) return v.toDate();
    if (v is DateTime) return v;
    if (v is int) {
      return DateTime.fromMillisecondsSinceEpoch(
        v < 100000000000 ? v * 1000 : v,
      );
    }
    if (v is double) return dateTime(v.toInt());
    if (v is String) {
      final s = v.trim();
      if (s.isEmpty) return null;
      return DateTime.tryParse(s) ?? _dmy(s);
    }
    return null;
  }

  static DateTime? _dmy(String s) {
    final m = RegExp(
      r'^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})(?:[ T]+(\d{1,2}):(\d{2}))?',
    ).firstMatch(s);
    if (m == null) return null;
    return DateTime(
      int.parse(m[3]!),
      int.parse(m[2]!),
      int.parse(m[1]!),
      int.parse(m[4] ?? '0'),
      int.parse(m[5] ?? '0'),
    );
  }

  /// Chuỗi giờ "HH:mm" ghép vào [date].
  static DateTime? onDate(DateTime? date, dynamic time) {
    if (date == null || time is! String) return null;
    final m = RegExp(r'^\s*(\d{1,2})[:h](\d{2})').firstMatch(time);
    if (m == null) return null;
    return DateTime(
      date.year,
      date.month,
      date.day,
      int.parse(m[1]!),
      int.parse(m[2]!),
    );
  }

  /// start_time / end_time: ưu tiên giá trị đầy đủ, nếu chỉ là "HH:mm"
  /// thì ghép với session_date.
  static DateTime? resolve(dynamic value, DateTime? sessionDate) =>
      dateTime(value) ?? onDate(sessionDate, value);

  static String two(int v) => v.toString().padLeft(2, '0');
  static String fmtDate(DateTime d) => '${two(d.day)}/${two(d.month)}/${d.year}';
  static String fmtTime(DateTime d) => '${two(d.hour)}:${two(d.minute)}';
}

String? _cleanId(dynamic v) {
  if (v == null) return null;
  final s = v.toString().trim();
  if (s.isEmpty || s.toLowerCase() == 'null') return null;
  return s;
}

double? _num(dynamic v) {
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v.trim());
  return null;
}

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

    final sessionDate = SessionTimeParser.dateTime(data['session_date']);
    final parsedStart = SessionTimeParser.resolve(data['start_time'], sessionDate);
    final parsedEnd = SessionTimeParser.resolve(data['end_time'], sessionDate);
    final fallback = sessionDate ??
        SessionTimeParser.dateTime(data['created_at']) ??
        DateTime.now();
    final start = parsedStart ?? fallback;
    final end = parsedEnd ?? start;

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
      studentCount: _countStudents(
        data['monitored_students'] ?? data['monitored_student'],
      ),
    );
  }

  static int _countStudents(dynamic raw) {
    if (raw is! Map) return 0;
    final ids = <String>{};
    for (final v in raw.values) {
      if (v is! Map) continue;
      final id = _cleanId(v['student_id']);
      if (id != null) ids.add(id);
    }
    return ids.length;
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

  /// Chuỗi hiển thị dd/MM/yyyy, HH:mm (giữ nguyên để các màn khác dùng).
  final String date;
  final String start;
  final String end;

  /// Thời gian thật (null nếu dữ liệu không đọc được).
  final DateTime? dateAt;
  final DateTime? startAt;
  final DateTime? endAt;

  final int size;
  final int presentStudent;

  /// Lấy từ `class_attention_score` của session.
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
    this.dateAt,
    this.startAt,
    this.endAt,
    required this.size,
    this.presentStudent = 0,
    this.avgAttentionScore = 0.0,
    this.note = '',
    required this.status,
    this.subject = '',
    this.period = '',
    this.sessionType = '',
  });

  bool get isEnded => status == 'Đã kết thúc';

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
    DateTime? dateAt,
    DateTime? startAt,
    DateTime? endAt,
    int? size,
    int? presentStudent,
    double? avgAttentionScore,
    String? note,
    String? status,
    String? subject,
    String? period,
    String? sessionType,
  }) {
    final newSize = size ?? this.size;
    final newPresent = presentStudent ?? this.presentStudent;
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
      dateAt: dateAt ?? this.dateAt,
      startAt: startAt ?? this.startAt,
      endAt: endAt ?? this.endAt,
      size: newSize,
      // Số có mặt không bao giờ vượt sĩ số
      presentStudent: newPresent > newSize ? newSize : newPresent,
      avgAttentionScore: avgAttentionScore ?? this.avgAttentionScore,
      note: note ?? this.note,
      status: status ?? this.status,
      subject: subject ?? this.subject,
      period: period ?? this.period,
      sessionType: sessionType ?? this.sessionType,
    );
  }

  factory SessionModel.fromFirestore(
    DocumentSnapshot doc, {
    String className = 'Lớp học',
    int classSize = 0,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    // ── Ngày giờ ────────────────────────────────────────────────
    final sessionDate = SessionTimeParser.dateTime(data['session_date']);
    final startAt = SessionTimeParser.resolve(data['start_time'], sessionDate);
    final endAt = SessionTimeParser.resolve(data['end_time'], sessionDate);
    final dateAt = startAt ?? sessionDate ?? endAt;

    // ── Trạng thái ──────────────────────────────────────────────
    final now = DateTime.now();
    final effectiveEnd =
        endAt ?? startAt?.add(const Duration(minutes: 45)); // thiếu end_time
    String status;
    if (startAt != null && effectiveEnd != null) {
      if (now.isBefore(startAt)) {
        status = 'Sắp diễn ra';
      } else if (now.isAfter(effectiveEnd)) {
        status = 'Đã kết thúc';
      } else {
        status = 'Đang diễn ra';
      }
    } else if (dateAt != null) {
      final today = DateTime(now.year, now.month, now.day);
      final day = DateTime(dateAt.year, dateAt.month, dateAt.day);
      if (day.isBefore(today)) {
        status = 'Đã kết thúc';
      } else if (day.isAfter(today)) {
        status = 'Sắp diễn ra';
      } else {
        status = 'Hôm nay';
      }
    } else {
      status = 'Chưa rõ';
    }

    // ── Học sinh trong phiên (map hoặc list, chấp nhận sai chính tả) ──
    final dynamic raw = data['monitored_students'] ??
        data['mnoitored_students'] ??
        data['monitored_student'] ??
        data['mnoitored_student'] ??
        data['students'];
    final Iterable entries = raw is Map
        ? raw.values
        : raw is List
            ? raw
            : const [];
    final ids = <String>{};
    final presentIds = <String>{};
    for (final e in entries) {
      if (e is! Map) continue;
      final id = _cleanId(e['student_id']);
      if (id == null) continue;
      ids.add(id);
      if (e['is_present'] == true) presentIds.add(id);
    }

    final int presentCount =
        (data['present_student'] as num?)?.toInt() ?? presentIds.length;
    final int size = classSize > 0
        ? classSize
        : (ids.isNotEmpty ? ids.length : presentCount);

    // ── Độ tập trung của cả lớp ─────────────────────────────────
    final double attention = _num(data['class_attention_score']) ??
        _num(data['avg_attention_score']) ??
        0.0;

    String firstText(List<String> keys, [String fallback = '']) {
      for (final k in keys) {
        final v = data[k];
        if (v != null && v.toString().trim().isNotEmpty) {
          return v.toString().trim();
        }
      }
      return fallback;
    }

    return SessionModel(
      id: doc.id,
      classId: data['class_id']?.toString() ?? '',
      teacherId: data['teacher_id']?.toString() ?? '',
      classroomId: data['classroom_id']?.toString() ?? '',
      cameraId: firstText(['camera_id']),
      className: className,
      room: firstText(['room', 'classroom_id', 'camera_id'], 'N/A'),
      date: dateAt != null ? SessionTimeParser.fmtDate(dateAt) : '--/--/----',
      start: startAt != null ? SessionTimeParser.fmtTime(startAt) : '--:--',
      end: endAt != null ? SessionTimeParser.fmtTime(endAt) : '--:--',
      dateAt: dateAt,
      startAt: startAt,
      endAt: endAt,
      size: size,
      presentStudent: presentCount > size ? size : presentCount,
      avgAttentionScore: attention,
      note: data['note']?.toString() ?? '',
      status: status,
      subject: firstText(['subject']),
      period: firstText(['period']),
      sessionType: firstText(['sesion_type', 'session_type']),
    );
  }
}
