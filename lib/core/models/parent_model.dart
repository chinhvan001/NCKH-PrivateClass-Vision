import 'package:cloud_firestore/cloud_firestore.dart';

/// Model thông tin lớp học của học sinh (lấy từ classes2 và teachers)
class ChildClass {
  final String id;
  final String name;
  final String schoolYear;
  final String teacherName;

  ChildClass({
    required this.id,
    required this.name,
    required this.schoolYear,
    this.teacherName = '',
  });

  String get display {
    if (name.isNotEmpty && schoolYear.isNotEmpty) {
      return '$name · Năm học $schoolYear';
    }
    return name.isNotEmpty ? name : 'Chưa xếp lớp';
  }
}

/// Model học sinh được liên kết với phụ huynh (lấy từ students2)
class LinkedChild {
  final String id;
  final String name;
  final String birthday;
  final String gender;
  final List<ChildClass> classes;
  final String? parentName;
  final String? parentPhone;
  final bool isActive;

  LinkedChild({
    required this.id,
    required this.name,
    required this.birthday,
    required this.gender,
    required this.classes,
    this.parentName,
    this.parentPhone,
    this.isActive = true,
  });

  String get statusDisplay => isActive ? 'Đang học' : 'Nghỉ học';

  String get shortName {
    final parts = name.trim().split(' ');
    return parts.isNotEmpty ? parts.last : name;
  }

  String get classDisplay =>
      classes.isNotEmpty ? classes.first.display : 'Chưa xếp lớp';

  String get teacherDisplay =>
      classes.isNotEmpty && classes.first.teacherName.isNotEmpty
          ? classes.first.teacherName
          : 'Chưa cập nhật';
}

/// Model hồ sơ phụ huynh (lấy từ collection parents / parent)
class ParentModel {
  final String id;
  final String name;
  final String email;
  final String phoneNumber;
  final bool isActive;

  ParentModel({
    required this.id,
    required this.name,
    required this.email,
    required this.phoneNumber,
    this.isActive = true,
  });

  factory ParentModel.fromFirestore(DocumentSnapshot doc) {
    final data = (doc.data() as Map<String, dynamic>?) ?? {};
    return ParentModel(
      id: doc.id,
      name: (data['name'] ?? '').toString(),
      email: (data['email'] ?? '').toString(),
      phoneNumber: (data['phone_number'] ?? data['parent_phonenumber'] ?? '').toString(),
      isActive: data['is_active'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'name': name,
      'email': email,
      'phone_number': phoneNumber,
      'is_active': isActive,
    };
  }
}

/// Model thông tin buổi học (lấy từ collection sessions)
class SessionInfo {
  final String id;
  final String classId;
  final String sessionDate;
  final String subject;
  final String room;
  final int period;
  final String sessionType;
  final String status;

  const SessionInfo({
    required this.id,
    required this.classId,
    required this.sessionDate,
    required this.subject,
    required this.room,
    required this.period,
    required this.sessionType,
    required this.status,
  });

  factory SessionInfo.fromFirestore(DocumentSnapshot doc) {
    final d = (doc.data() as Map<String, dynamic>?) ?? {};
    return SessionInfo(
      id: doc.id,
      classId: (d['class_id'] ?? '').toString(),
      sessionDate: (d['session_date'] ?? '').toString(),
      subject: (d['subject'] ?? 'Môn học').toString(),
      room: (d['room'] ?? '').toString(),
      period: (d['period'] is num) ? (d['period'] as num).toInt() : 1,
      sessionType: (d['session_type'] ?? '').toString(),
      status: (d['status'] ?? '').toString(),
    );
  }
}

/// Model kết quả buổi học của học sinh (lấy từ session_results -> result_map)
class StudentSessionResult {
  final String sessionId;
  final String seatId;
  final int concentration;
  final int interaction;
  final String status;
  final DateTime? capturedAt;

  const StudentSessionResult({
    required this.sessionId,
    required this.seatId,
    this.concentration = 0,
    this.interaction = 0,
    this.status = 'unknown',
    this.capturedAt,
  });
}

/// Model tổng hợp số liệu điểm danh cho AttendanceDetailScreen & HomeScreen
class AttendanceSummary {
  final int totalSessions;
  final int attendedSessions;
  final int excusedAbsences;
  final int unexcusedAbsences;
  final int lateSessions;
  final List<AbsenceRecord> absenceList;

  const AttendanceSummary({
    this.totalSessions = 0,
    this.attendedSessions = 0,
    this.excusedAbsences = 0,
    this.unexcusedAbsences = 0,
    this.lateSessions = 0,
    this.absenceList = const [],
  });

  double get attendanceRate =>
      totalSessions > 0 ? (attendedSessions / totalSessions) * 100 : 0.0;
}

/// Model bản ghi vắng / đi muộn
class AbsenceRecord {
  final String date;
  final String type;
  final String reason;

  const AbsenceRecord({
    required this.date,
    required this.type,
    required this.reason,
  });
}

/// Loại thông báo phụ huynh
enum NotificationType {
  /// Học sinh vắng mặt (is_present == false) ở buổi học đã kết thúc
  absence,

  /// Nhắc nhở từ giáo viên (note của buổi học)
  reminder,
}

/// Trạng thái của một tiết học so với thời điểm hiện tại
enum SessionState { upcoming, ongoing, ended }

/// Một tiết học của học sinh (lấy từ sessions, kèm dữ liệu của đúng ghế học sinh đó)
class StudentSession {
  final String id;
  final String classId;
  final String className;

  /// Ngày học (chỉ phần ngày, giờ = 00:00)
  final DateTime date;
  final DateTime? startTime;
  final DateTime? endTime;
  final int period;
  final String subject;
  final String room;
  final String teacherName;
  final bool isPresent;

  /// Chỉ số tập trung 0-100 của học sinh ở tiết này (null nếu chưa có)
  final double? attentionScore;

  /// Trường status của buổi học đã ở trạng thái kết thúc
  final bool statusEnded;

  const StudentSession({
    required this.id,
    required this.classId,
    required this.className,
    required this.date,
    required this.period,
    required this.subject,
    required this.isPresent,
    this.startTime,
    this.endTime,
    this.room = '',
    this.teacherName = '',
    this.attentionScore,
    this.statusEnded = false,
  });

  SessionState stateAt(DateTime now) {
    final end = endTime;
    if (end != null) {
      if (!end.isAfter(now)) return SessionState.ended;
      final start = startTime;
      if (start != null && !start.isAfter(now)) return SessionState.ongoing;
      return SessionState.upcoming;
    }
    if (statusEnded) return SessionState.ended;
    final today = DateTime(now.year, now.month, now.day);
    return date.isBefore(today) ? SessionState.ended : SessionState.upcoming;
  }

  /// Vắng mặt: tiết đã kết thúc mà học sinh không có mặt
  bool isAbsentAt(DateTime now) =>
      !isPresent && stateAt(now) == SessionState.ended;
}

/// Model thông báo phụ huynh (trích xuất từ sessions)
class ParentNotification {
  final String id;
  final String sessionId;
  final NotificationType type;

  /// Thời điểm phát sinh thông báo (giờ kết thúc buổi học) dùng để tính "x phút trước"
  final DateTime timestamp;

  final DateTime? startTime;
  final DateTime? endTime;
  final int? period;
  final String subject;
  final String teacherName;
  final String room;

  /// Nội dung nhắc nhở của giáo viên (chỉ có với type == reminder)
  final String note;

  const ParentNotification({
    required this.id,
    required this.sessionId,
    required this.type,
    required this.timestamp,
    this.startTime,
    this.endTime,
    this.period,
    this.subject = '',
    this.teacherName = '',
    this.room = '',
    this.note = '',
  });
}
