import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

import '../models/parent_model.dart';

class ParentService {
  ParentService({FirebaseFirestore? db}) : _injectedDb = db;

  final FirebaseFirestore? _injectedDb;
  FirebaseFirestore get _db => _injectedDb ?? FirebaseFirestore.instance;

  Future<ParentModel?> getParent(String uid) async {
    try {
      var doc = await _db.collection('parents').doc(uid).get();
      if (!doc.exists) {
        doc = await _db.collection('parent').doc(uid).get();
      }
      return doc.exists ? ParentModel.fromFirestore(doc) : null;
    } catch (e) {
      debugPrint('Lỗi tải thông tin parent: $e');
      return null;
    }
  }

  Stream<List<LinkedChild>> watchChildren({required String uid, String? email}) {
    return _db
        .collection('students2')
        .where('parent_id', isEqualTo: uid)
        .snapshots()
        .asyncMap((snap) async {
      final List<LinkedChild> children = [];
      for (final doc in snap.docs) {
        final child = await _buildChild(doc);
        children.add(child);
      }
      children.sort((a, b) => a.name.compareTo(b.name));
      return children;
    });
  }

  Future<LinkedChild> _buildChild(DocumentSnapshot doc) async {
    final sData = (doc.data() as Map<String, dynamic>?) ?? {};
    final fullName = (sData['full_name'] ??
            sData['fullname'] ??
            sData['name'] ??
            'Học sinh')
        .toString();
    final classList = await _fetchClassesForStudent(doc.id);

    return LinkedChild(
      id: doc.id,
      name: fullName,
      birthday: _formatDate(sData['birthday']),
      gender: (sData['gender'] ?? '').toString(),
      classes: classList,
      parentName: (sData['parent_name'] ?? '').toString(),
      parentPhone: (sData['parent_phonenumber'] ?? '').toString(),
    );
  }

  Future<List<ChildClass>> _fetchClassesForStudent(String studentId) async {
    final List<ChildClass> result = [];

    try {
      final classSnap = await _db.collection('classes2').get();

      for (final classDoc in classSnap.docs) {
        final cData = classDoc.data();
        final rawSeatmap = cData['seat_map'] ?? cData['seatmap'];
        final Map<String, dynamic>? seatmap =
            rawSeatmap != null ? Map<String, dynamic>.from(rawSeatmap as Map) : null;

        bool isEnrolled = false;
        if (seatmap != null) {
          for (final seat in seatmap.values) {
            if (seat is Map && seat['student_id']?.toString() == studentId) {
              isEnrolled = true;
              break;
            }
          }
        }

        if (isEnrolled) {
          String teacherName = '';
          final teacherId =
              (cData['teacher_id'] ?? cData['teacherId'] ?? '').toString();

          if (teacherId.isNotEmpty) {
            var teacherDoc =
                await _db.collection('teachers').doc(teacherId).get();
            if (!teacherDoc.exists) {
              teacherDoc = await _db.collection('teacher').doc(teacherId).get();
            }
            final tData = teacherDoc.data();
            teacherName = (tData?['name'] ?? '').toString();
          }

          final className = (cData['class_name'] ??
                  cData['name'] ??
                  cData['className'] ??
                  classDoc.id)
              .toString();

          final schoolYear = (cData['school_year'] ??
                  cData['schoolYear'] ??
                  cData['year'] ??
                  '')
              .toString();

          result.add(
            ChildClass(
              id: classDoc.id,
              name: className,
              schoolYear: schoolYear,
              teacherName: teacherName,
            ),
          );
        }
      }
    } catch (e) {
      debugPrint('Lỗi quét lớp: $e');
    }

    return result;
  }

  Future<String?> getSeatIdForStudent({
    required String classId,
    required String studentId,
  }) async {
    try {
      final doc = await _db.collection('classes2').doc(classId).get();
      if (!doc.exists) return null;

      final data = doc.data() ?? {};
      final rawSeatmap = data['seat_map'] ?? data['seatmap'];
      final Map<String, dynamic>? seatmap =
          rawSeatmap != null ? Map<String, dynamic>.from(rawSeatmap as Map) : null;

      if (seatmap != null) {
        for (final entry in seatmap.entries) {
          final seatData = entry.value;
          if (seatData is Map &&
              seatData['student_id']?.toString() == studentId) {
            return (seatData['seat_id'] ?? entry.key).toString();
          }
        }
      }
    } catch (e) {
      debugPrint('Lỗi tìm seatId: $e');
    }
    return null;
  }

  Future<AttendanceSummary> getAttendanceSummary({
    required String studentId,
    String? classId,
  }) async {
    try {
      String? targetSeatId;
      if (classId != null && classId.isNotEmpty) {
        targetSeatId =
            await getSeatIdForStudent(classId: classId, studentId: studentId);
      }

      final resultsSnap = await _db.collection('session_results').get();
      int total = 0;
      int attended = 0;
      int excused = 0;
      int unexcused = 0;
      int lateCount = 0;
      final List<AbsenceRecord> absences = [];

      for (final doc in resultsSnap.docs) {
        final data = doc.data();
        final rawResultMap = data['result_map'];
        if (rawResultMap == null) continue;

        final Map<String, dynamic> resultMap =
            Map<String, dynamic>.from(rawResultMap as Map);

        Map<String, dynamic>? studentMetric;
        if (targetSeatId != null && resultMap.containsKey(targetSeatId)) {
          final m = resultMap[targetSeatId];
          if (m is Map) studentMetric = Map<String, dynamic>.from(m);
        } else {
          for (final seat in resultMap.values) {
            if (seat is Map &&
                (seat['student_id']?.toString() == studentId ||
                    seat['seat_id']?.toString() == targetSeatId)) {
              studentMetric = Map<String, dynamic>.from(seat);
              break;
            }
          }
        }

        if (studentMetric != null) {
          total++;
          final status =
              (studentMetric['status'] ?? '').toString().toLowerCase();
          final captureTime = data['captured_at'];
          String dateStr = '';
          if (captureTime is Timestamp) {
            final dt = captureTime.toDate();
            dateStr =
                '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
          }

          if (status == 'absent_excused') {
            excused++;
            absences.add(AbsenceRecord(
              date: dateStr,
              type: 'Vắng có phép',
              reason: 'Có đơn xin phép',
            ));
          } else if (status == 'absent') {
            unexcused++;
            absences.add(AbsenceRecord(
              date: dateStr,
              type: 'Vắng không phép',
              reason: 'Không phép',
            ));
          } else if (status == 'late') {
            lateCount++;
            attended++;
          } else {
            attended++;
          }
        }
      }

      return AttendanceSummary(
        totalSessions: total,
        attendedSessions: attended,
        excusedAbsences: excused,
        unexcusedAbsences: unexcused,
        lateSessions: lateCount,
        absenceList: absences,
      );
    } catch (e) {
      debugPrint('Lỗi tính attendance: $e');
      return const AttendanceSummary();
    }
  }

  String _formatDate(dynamic value) {
    if (value is Timestamp) {
      final d = value.toDate();
      final dd = d.day.toString().padLeft(2, '0');
      final mm = d.month.toString().padLeft(2, '0');
      return '$dd/$mm/${d.year}';
    }
    return value?.toString() ?? '';
  }
}