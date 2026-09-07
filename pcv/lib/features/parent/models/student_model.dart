import 'package:cloud_firestore/cloud_firestore.dart';

class StudentModel {
  final String id;
  final String name;
  final String className;
  final String schoolName;
  final String teacherName;
  final String dateOfBirth;
  final String parentPhone;
  final String parentEmail;

  /// Tập trung trung bình (%) — tính từ sessions
  final int avgFocusPercent;

  /// Tổng buổi học trong tháng
  final int totalSessions;

  /// Số buổi có mặt
  final int presentSessions;

  /// Số buổi vắng có phép
  final int excusedSessions;

  /// Số buổi vắng không phép
  final int absentSessions;

  /// Số buổi đi muộn
  final int lateSessions;

  /// Giờ buổi học tiếp theo (VD: '15:30')
  final String nextSessionTime;

  const StudentModel({
    required this.id,
    required this.name,
    required this.className,
    required this.schoolName,
    required this.teacherName,
    required this.dateOfBirth,
    required this.parentPhone,
    required this.parentEmail,
    required this.avgFocusPercent,
    required this.totalSessions,
    required this.presentSessions,
    required this.excusedSessions,
    required this.absentSessions,
    required this.lateSessions,
    required this.nextSessionTime,
  });

  factory StudentModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return StudentModel(
      id: doc.id,
      name: d['name'] as String? ?? '',
      className: d['className'] as String? ?? '',
      schoolName: d['schoolName'] as String? ?? '',
      teacherName: d['teacherName'] as String? ?? '',
      dateOfBirth: d['dateOfBirth'] as String? ?? '',
      parentPhone: d['parentPhone'] as String? ?? '',
      parentEmail: d['parentEmail'] as String? ?? '',
      avgFocusPercent: (d['avgFocusPercent'] as num?)?.toInt() ?? 0,
      totalSessions: (d['totalSessions'] as num?)?.toInt() ?? 0,
      presentSessions: (d['presentSessions'] as num?)?.toInt() ?? 0,
      excusedSessions: (d['excusedSessions'] as num?)?.toInt() ?? 0,
      absentSessions: (d['absentSessions'] as num?)?.toInt() ?? 0,
      lateSessions: (d['lateSessions'] as num?)?.toInt() ?? 0,
      nextSessionTime: d['nextSessionTime'] as String? ?? '--:--',
    );
  }

  Map<String, dynamic> toMap() => {
    'name': name,
    'className': className,
    'schoolName': schoolName,
    'teacherName': teacherName,
    'dateOfBirth': dateOfBirth,
    'parentPhone': parentPhone,
    'parentEmail': parentEmail,
    'avgFocusPercent': avgFocusPercent,
    'totalSessions': totalSessions,
    'presentSessions': presentSessions,
    'excusedSessions': excusedSessions,
    'absentSessions': absentSessions,
    'lateSessions': lateSessions,
    'nextSessionTime': nextSessionTime,
  };
}
