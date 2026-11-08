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
      isActive: sData['is_active'] as bool? ?? true,
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

  /// Lấy thông báo của một học sinh từ collection sessions.
  ///
  /// Cách đọc dữ liệu (tối ưu số lần đọc):
  /// - Chỉ truy vấn các buổi học thuộc lớp của học sinh (`class_id`), không quét cả collection.
  /// - Mỗi buổi chỉ lấy đúng ghế có `student_id` trùng học sinh.
  /// - Tên giáo viên chỉ đọc khi thật sự có thông báo và được cache theo `teacher_id`.
  ///
  /// Quy tắc:
  /// - Vắng mặt: `is_present == false` và buổi học ĐÃ kết thúc (tránh báo nhầm buổi chưa diễn ra).
  /// - Nhắc nhở: `note` không rỗng (null, "", '""' đều bị bỏ qua).
  Future<List<ParentNotification>> getNotificationsForStudent({
    required String studentId,
    required List<String> classIds,
  }) async {
    final ids = classIds.where((e) => e.isNotEmpty).toSet().toList();
    if (ids.isEmpty) return [];

    try {
      final docs = <QueryDocumentSnapshot<Map<String, dynamic>>>[];
      // whereIn tối đa 30 giá trị nên chia nhóm
      for (var i = 0; i < ids.length; i += 30) {
        final chunk = ids.sublist(i, i + 30 > ids.length ? ids.length : i + 30);
        final col = _db.collection('sessions');
        final snap = chunk.length == 1
            ? await col.where('class_id', isEqualTo: chunk.first).get()
            : await col.where('class_id', whereIn: chunk).get();
        docs.addAll(snap.docs);
      }

      final now = DateTime.now();
      final teacherCache = <String, String>{};
      final result = <ParentNotification>[];

      for (final doc in docs) {
        final data = doc.data();

        final rawMonitored = data['monitored_students'] ?? data['mnoitored_student'];
        if (rawMonitored is! Map) continue;

        // Tìm ghế của học sinh trong buổi học
        Map? seat;
        for (final v in rawMonitored.values) {
          if (v is Map && v['student_id']?.toString() == studentId) {
            seat = v;
            break;
          }
        }
        if (seat == null) continue;

        final startTime = _toDate(data['start_time']) ?? _toDate(data['session_date']);
        final endTime = _toDate(data['end_time']);

        final isPresent = seat['is_present'] == true;
        final note = (seat['note'] ?? '').toString().trim();
        final hasNote = note.isNotEmpty && note != '""';
        final isAbsent = !isPresent && _hasEnded(data, startTime, endTime, now);

        if (!isAbsent && !hasNote) continue;

        final timestamp = endTime ?? startTime ?? now;
        final subject = _subjectOf(doc.id, data);
        final period = (data['period'] is num) ? (data['period'] as num).toInt() : null;
        final room = (data['room'] ?? '').toString();
        final teacherName = await _teacherName(
          (data['teacher_id'] ?? '').toString(),
          teacherCache,
        );

        ParentNotification build(NotificationType type, String suffix, {String note = ''}) {
          return ParentNotification(
            id: '${doc.id}_$suffix',
            sessionId: doc.id,
            type: type,
            timestamp: timestamp,
            startTime: startTime,
            endTime: endTime,
            period: period,
            subject: subject,
            teacherName: teacherName,
            room: room,
            note: note,
          );
        }

        if (isAbsent) {
          result.add(build(NotificationType.absence, 'absent'));
        }
        if (hasNote) {
          result.add(build(NotificationType.reminder, 'note', note: note));
        }
      }

      result.sort((a, b) => b.timestamp.compareTo(a.timestamp));
      return result;
    } catch (e) {
      debugPrint('--> [Notification] Lỗi trích xuất thông báo: $e');
      rethrow;
    }
  }

  /// Buổi học đã kết thúc: ưu tiên end_time, không có thì xét status, cuối cùng là ngày học
  bool _hasEnded(
    Map<String, dynamic> data,
    DateTime? start,
    DateTime? end,
    DateTime now,
  ) {
    if (end != null) return !end.isAfter(now);
    final status = (data['status'] ?? '').toString().toLowerCase();
    if (const ['completed', 'ended', 'finished', 'done', 'closed'].contains(status)) {
      return true;
    }
    if (start != null) {
      final today = DateTime(now.year, now.month, now.day);
      return start.isBefore(today);
    }
    return false;
  }

  String _subjectOf(String docId, Map<String, dynamic> data) {
    final subject = (data['subject'] ?? '').toString().trim();
    if (subject.isNotEmpty) return subject;
    final id = docId.toLowerCase();
    if (id.contains('toan')) return 'Toán';
    if (id.contains('van')) return 'Ngữ văn';
    if (id.contains('anh')) return 'Tiếng Anh';
    return 'Buổi học';
  }

  Future<String> _teacherName(String teacherId, Map<String, String> cache) async {
    if (teacherId.isEmpty) return '';
    final cached = cache[teacherId];
    if (cached != null) return cached;

    String name = '';
    try {
      var doc = await _db.collection('teachers').doc(teacherId).get();
      if (!doc.exists) {
        doc = await _db.collection('teacher').doc(teacherId).get();
      }
      name = (doc.data()?['name'] ?? '').toString();
    } catch (e) {
      debugPrint('Lỗi tải giáo viên $teacherId: $e');
    }
    cache[teacherId] = name;
    return name;
  }

  DateTime? _toDate(dynamic v) {
    if (v is Timestamp) return v.toDate();
    if (v is DateTime) return v;
    if (v is String) return DateTime.tryParse(v);
    return null;
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