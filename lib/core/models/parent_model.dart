import 'package:cloud_firestore/cloud_firestore.dart';

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

enum NotificationType {
  absence,
  reminder,
}

enum SessionState { upcoming, ongoing, ended }

class StudentSession {
  final String id;
  final String classId;
  final String className;
  final DateTime date;
  final DateTime? startTime;
  final DateTime? endTime;
  final int period;
  final String subject;
  final String room;
  final String teacherName;
  final bool isPresent;
  final double? attentionScore;
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

  bool isAbsentAt(DateTime now) =>
      !isPresent && stateAt(now) == SessionState.ended;
}

class ParentNotification {
  final String id;
  final String sessionId;
  final NotificationType type;
  final DateTime timestamp;
  final DateTime? startTime;
  final DateTime? endTime;
  final int? period;
  final String subject;
  final String teacherName;
  final String room;
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

class HomeStats {
  final String nextSessionTime;
  final double avgAttention;
  final int totalEnded;
  final int attended;
  final int excusedAbsence;
  final int unexcusedAbsence;
  final int lateCount;
  final int notificationCount;

  const HomeStats({
    this.nextSessionTime = '--:--',
    this.avgAttention = 0.0,
    this.totalEnded = 0,
    this.attended = 0,
    this.excusedAbsence = 0,
    this.unexcusedAbsence = 0,
    this.lateCount = 0,
    this.notificationCount = 0,
  });

  String get attendanceDisplay => '$attended/$totalEnded';
  int get attendancePercent =>
      totalEnded > 0 ? ((attended / totalEnded) * 100).round() : 0;
  int get attentionPercent => avgAttention.round().clamp(0, 100);
}

/// Chi tiết mức độ tập trung của 1 tiết/ngày cụ thể trong một môn
class SubjectDailyFocus {
  final String date;
  final int period;
  final int percent;
  final bool isPresent;

  const SubjectDailyFocus({
    required this.date,
    required this.period,
    required this.percent,
    required this.isPresent,
  });
}

/// Thống kê đầy đủ của một môn học (dùng cho cả Trang chủ và màn hình Chi tiết môn)
class SubjectFocus {
  final String subject;
  final int percent;
  final String teacherName;
  final int totalSessions;
  final int attendedSessions;
  final int absentSessions;
  final List<SubjectDailyFocus> dailyRecords;

  const SubjectFocus({
    required this.subject,
    required this.percent,
    this.teacherName = 'Chưa cập nhật',
    this.totalSessions = 0,
    this.attendedSessions = 0,
    this.absentSessions = 0,
    this.dailyRecords = const [],
  });
}

class OverviewStats {
  final List<SubjectFocus> subjects;
  final int totalSessions;
  final int attendedSessions;
  final int excusedAbsences;
  final int unexcusedAbsences;

  const OverviewStats({
    this.subjects = const [],
    this.totalSessions = 0,
    this.attendedSessions = 0,
    this.excusedAbsences = 0,
    this.unexcusedAbsences = 0,
  });
}