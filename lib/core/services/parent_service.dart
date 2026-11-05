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

  /// Lấy danh sách thông báo cho học sinh trực tiếp từ collection sessions
  Future<List<ParentNotification>> getNotificationsForStudent({
    required String studentId,
    String? classId,
  }) async {
    try {
      debugPrint('--> [Notification] Quét sessions: studentId=$studentId, classId=$classId');

      String? targetSeatId;
      if (classId != null && classId.isNotEmpty) {
        targetSeatId = await getSeatIdForStudent(classId: classId, studentId: studentId);
      }

      Query query = _db.collection('sessions');
      if (classId != null && classId.isNotEmpty) {
        query = query.where('class_id', isEqualTo: classId);
      }

      final querySnapshot = await query.get();
      final List<ParentNotification> notifications = [];

      for (final doc in querySnapshot.docs) {
        final data = doc.data() as Map<String, dynamic>;

        DateTime sessionTime = DateTime.now();
        if (data['end_time'] is Timestamp) {
          sessionTime = (data['end_time'] as Timestamp).toDate();
        } else if (data['created_at'] is Timestamp) {
          sessionTime = (data['created_at'] as Timestamp).toDate();
        } else if (data['session_date'] is Timestamp) {
          sessionTime = (data['session_date'] as Timestamp).toDate();
        }

        final dateFormatted =
            '${sessionTime.day.toString().padLeft(2, '0')}/${sessionTime.month.toString().padLeft(2, '0')}/${sessionTime.year}';

        String subject = data['subject']?.toString() ?? '';
        if (subject.isEmpty) {
          final docIdLower = doc.id.toLowerCase();
          if (docIdLower.contains('toan')) {
            subject = 'Toán';
          } else if (docIdLower.contains('van')) {
            subject = 'Ngữ văn';
          } else if (docIdLower.contains('anh')) {
            subject = 'Tiếng Anh';
          } else {
            subject = 'Buổi học';
          }
        }

        final rawMonitored = data['monitored_students'] ?? data['mnoitored_student'];
        if (rawMonitored == null) continue;
        final monitoredStudents = Map<String, dynamic>.from(rawMonitored as Map);

        for (final entry in monitoredStudents.entries) {
          final seatId = entry.key;
          final seatData = entry.value;
          if (seatData is! Map) continue;

          final sId = seatData['student_id']?.toString() ?? '';

          final bool isMatched = (sId == studentId) ||
              (targetSeatId != null && seatId.toUpperCase() == targetSeatId.toUpperCase());

          if (!isMatched) continue;

          final isPresent = seatData['is_present'] == true;
          final isAttention = seatData['is_attention'] == true;
          final double attentionScore = (seatData['attention_score'] is num)
              ? (seatData['attention_score'] as num).toDouble()
              : 0.0;
          final note = seatData['note']?.toString() ?? '';

          // 1. Điểm danh
          if (!isPresent) {
            notifications.add(
              ParentNotification(
                id: '${doc.id}_${seatId}_absent',
                sessionId: doc.id,
                title: 'Cảnh báo vắng mặt',
                message: 'Bé vắng mặt trong buổi học môn $subject ngày $dateFormatted.',
                type: NotificationType.attendance,
                timestamp: sessionTime,
                isPresent: false,
                attentionScore: attentionScore,
              ),
            );
          } else {
            notifications.add(
              ParentNotification(
                id: '${doc.id}_${seatId}_present',
                sessionId: doc.id,
                title: 'Điểm danh buổi học',
                message: 'Bé đã có mặt đầy đủ trong tiết $subject ngày $dateFormatted.',
                type: NotificationType.attendance,
                timestamp: sessionTime,
                isPresent: true,
                attentionScore: attentionScore,
              ),
            );

            // 2. Mức độ tập trung
            if (!isAttention || attentionScore < 50) {
              notifications.add(
                ParentNotification(
                  id: '${doc.id}_${seatId}_att_warn',
                  sessionId: doc.id,
                  title: 'Nhắc nhở chú ý',
                  message: 'Mức độ tập trung của bé trong tiết $subject đạt $attentionScore%, cần chú ý hơn.',
                  type: NotificationType.attentionWarning,
                  timestamp: sessionTime,
                  isPresent: true,
                  attentionScore: attentionScore,
                ),
              );
            } else if (attentionScore >= 80) {
              notifications.add(
                ParentNotification(
                  id: '${doc.id}_${seatId}_att_praise',
                  sessionId: doc.id,
                  title: 'Khen ngợi học tập',
                  message: 'Bé rất tập trung trong tiết $subject (đạt $attentionScore%). Tinh thần học tập rất tốt!',
                  type: NotificationType.attentionPraise,
                  timestamp: sessionTime,
                  isPresent: true,
                  attentionScore: attentionScore,
                ),
              );
            }
          }

          // 3. Ghi chú buổi học
          if (note.trim().isNotEmpty && note != '""') {
            notifications.add(
              ParentNotification(
                id: '${doc.id}_${seatId}_note',
                sessionId: doc.id,
                title: 'Ghi chú buổi học',
                message: 'Lời nhắn: "$note" ($subject - $dateFormatted)',
                type: NotificationType.note,
                timestamp: sessionTime,
                isPresent: isPresent,
                attentionScore: attentionScore,
              ),
            );
          }
        }
      }

      notifications.sort((a, b) => b.timestamp.compareTo(a.timestamp));
      return notifications;
    } catch (e) {
      debugPrint('--> [Notification] Lỗi trích xuất thông báo: $e');
      return [];
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