import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

import '../constants/firestore_constants.dart';
import '../models/parent_model.dart';
import '../models/student_model.dart';
import '../utils/firestore_parsers.dart';

class StudentAttendanceStats {
  final int totalSessions;
  final int attendedSessions;
  final int absentSessions;
  final double attendanceRate;
  final double avgAttentionScore;
  final bool isFrequentlyAbsent;
  final String warningMessage;

  const StudentAttendanceStats({
    required this.totalSessions,
    required this.attendedSessions,
    required this.absentSessions,
    required this.attendanceRate,
    required this.avgAttentionScore,
    required this.isFrequentlyAbsent,
    required this.warningMessage,
  });

  factory StudentAttendanceStats.empty() {
    return const StudentAttendanceStats(
      totalSessions: 0,
      attendedSessions: 0,
      absentSessions: 0,
      attendanceRate: 100.0,
      avgAttentionScore: 0.0,
      isFrequentlyAbsent: false,
      warningMessage: '',
    );
  }
}

class StudentFullProfile {
  final StudentModel student;
  final ParentModel? parent;
  final bool isParentLinked;
  final String parentDisplayName;
  final String parentPhone;
  final String parentEmail;
  final StudentAttendanceStats stats;

  const StudentFullProfile({
    required this.student,
    this.parent,
    required this.isParentLinked,
    required this.parentDisplayName,
    required this.parentPhone,
    required this.parentEmail,
    required this.stats,
  });
}

class StudentProfileService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<StudentFullProfile> getStudentFullProfile({
    required String studentId,
    required String classId,
    StudentModel? initialStudentModel,
  }) async {
    StudentModel student = initialStudentModel ??
        await _fetchStudentById(studentId, classId);

    final results = await Future.wait([
      _fetchParentInfo(student.parentId, student.parentEmail),
      _calculateAttendanceStats(studentId, classId),
    ]);

    final parentResult = results[0] as _ParentFetchResult;
    final stats = results[1] as StudentAttendanceStats;

    return StudentFullProfile(
      student: student,
      parent: parentResult.parent,
      isParentLinked: parentResult.isLinked,
      parentDisplayName: parentResult.displayName,
      parentPhone: parentResult.phone,
      parentEmail: parentResult.email,
      stats: stats,
    );
  }

  Future<StudentModel> _fetchStudentById(String studentId, String classId) async {
    try {
      final doc = await _firestore
          .collection(FirestoreConstants.students)
          .doc(studentId)
          .get();
      if (!doc.exists) {
        return StudentModel(
          id: studentId,
          name: 'Học sinh $studentId',
          short: 'HS',
        );
      }

      int? row;
      int? col;
      bool isStudying = true;

      // Read seat position from seatmap in classes2 document
      if (classId.isNotEmpty) {
        final classDoc = await _firestore
            .collection(FirestoreConstants.classes)
            .doc(classId)
            .get();
        if (classDoc.exists) {
          final classData = classDoc.data() ?? {};
          final rawSeatmap = classData['seatmap'] ?? classData['seat_map'];
          if (rawSeatmap is Map) {
            for (final entry in rawSeatmap.entries) {
              if (entry.value is Map) {
                final sid =
                    FirestoreParsers.cleanId(entry.value['student_id']);
                if (sid == studentId) {
                  row = (entry.value['row'] as num?)?.toInt();
                  col = (entry.value['column'] as num?)?.toInt();
                  break;
                }
              }
            }
          }
        }
      }

      return StudentModel.fromFirestore(
        doc,
        row: row,
        column: col,
        isStudying: isStudying,
      );
    } catch (e) {
      debugPrint('Lỗi _fetchStudentById: $e');
      return StudentModel(
        id: studentId,
        name: 'Học sinh',
        short: 'HS',
      );
    }
  }

  Future<_ParentFetchResult> _fetchParentInfo(
    String parentId,
    String parentEmail,
  ) async {
    try {
      DocumentSnapshot<Map<String, dynamic>>? parentDoc;

      if (parentId.isNotEmpty) {
        final doc = await _firestore.collection(FirestoreConstants.parents).doc(parentId).get();
        if (doc.exists) {
          parentDoc = doc;
        }
      }

      if (parentDoc == null && parentEmail.isNotEmpty) {
        final querySnap = await _firestore
            .collection(FirestoreConstants.parents)
            .where('email', isEqualTo: parentEmail.trim())
            .limit(1)
            .get();
        if (querySnap.docs.isNotEmpty) {
          parentDoc = querySnap.docs.first;
        }
      }

      if (parentDoc != null && parentDoc.exists) {
        final model = ParentModel.fromFirestore(parentDoc);
        final phone = model.phoneNumber.trim().isNotEmpty
            ? model.phoneNumber
            : 'Chưa cập nhật SĐT';
        return _ParentFetchResult(
          parent: model,
          isLinked: true,
          displayName: model.name.isNotEmpty ? model.name : 'Phụ huynh học sinh',
          phone: phone,
          email: model.email.isNotEmpty ? model.email : parentEmail,
        );
      }

      final emailDisplay = parentEmail.isNotEmpty ? parentEmail : 'Chưa có email';
      return _ParentFetchResult(
        parent: null,
        isLinked: false,
        displayName: 'Chưa liên kết tài khoản',
        phone: 'Chưa có số điện thoại',
        email: emailDisplay,
      );
    } catch (e) {
      debugPrint('Lỗi _fetchParentInfo: $e');
      return _ParentFetchResult(
        parent: null,
        isLinked: false,
        displayName: 'Chưa liên kết',
        phone: 'Chưa cập nhật',
        email: parentEmail,
      );
    }
  }

  Future<StudentAttendanceStats> _calculateAttendanceStats(
    String studentId,
    String classId,
  ) async {
    try {
      Query<Map<String, dynamic>> query =
          _firestore.collection(FirestoreConstants.sessions);
      if (classId.isNotEmpty) {
        query = query.where('class_id', isEqualTo: classId);
      }

      final sessionsSnap = await query.get();

      int total = 0;
      int attended = 0;
      int absent = 0;
      double totalAttentionScore = 0.0;
      int attentionCount = 0;

      for (var doc in sessionsSnap.docs) {
        final data = doc.data();

        // New schema: mnoitored_student Map keyed by seat_id
        final rawMonitored =
            data['mnoitored_student'] ?? data['monitored_student'];
        if (rawMonitored is Map) {
          for (final entry in rawMonitored.entries) {
            if (entry.value is Map &&
                FirestoreParsers.cleanId(entry.value['student_id']) ==
                    studentId) {
              total++;
              final bool isPresent = entry.value['is_present'] == true;
              if (isPresent) {
                attended++;
                final score =
                    (entry.value['attention_score'] as num?)?.toDouble();
                if (score != null && score > 0) {
                  totalAttentionScore += score;
                  attentionCount++;
                }
              } else {
                absent++;
              }
              break;
            }
          }
          continue;
        }

        // Legacy: students List
        final rawStudents = data['students'];
        if (rawStudents is! List) continue;
        for (var item in rawStudents) {
          if (item is Map && item['student_id'] == studentId) {
            total++;
            final bool isPresent = item['is_present'] == true;
            if (isPresent) {
              attended++;
              final score = (item['attention_score'] as num?)?.toDouble();
              if (score != null && score > 0) {
                totalAttentionScore += score;
                attentionCount++;
              }
            } else {
              absent++;
            }
            break;
          }
        }
      }

      if (total == 0) {
        return StudentAttendanceStats.empty();
      }

      final double attendanceRate = (attended / total) * 100.0;
      final double avgAttention = attentionCount > 0
          ? double.parse((totalAttentionScore / attentionCount).toStringAsFixed(1))
          : 0.0;

      final bool isFrequentlyAbsent =
          absent >= 3 || (total >= 3 && (absent / total) >= 0.20);

      String warningMessage = '';
      if (isFrequentlyAbsent) {
        final double absentRate = (absent / total) * 100.0;
        warningMessage =
            'Học sinh đã vắng $absent buổi trên tổng số $total buổi học (${absentRate.toStringAsFixed(0)}%). Giáo viên cần liên hệ phụ huynh để tìm hiểu lý do và theo dõi sát sao.';
      }

      return StudentAttendanceStats(
        totalSessions: total,
        attendedSessions: attended,
        absentSessions: absent,
        attendanceRate: double.parse(attendanceRate.toStringAsFixed(1)),
        avgAttentionScore: avgAttention,
        isFrequentlyAbsent: isFrequentlyAbsent,
        warningMessage: warningMessage,
      );
    } catch (e) {
      debugPrint('Lỗi _calculateAttendanceStats: $e');
      return StudentAttendanceStats.empty();
    }
  }
}

class _ParentFetchResult {
  final ParentModel? parent;
  final bool isLinked;
  final String displayName;
  final String phone;
  final String email;

  _ParentFetchResult({
    required this.parent,
    required this.isLinked,
    required this.displayName,
    required this.phone,
    required this.email,
  });
}


