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

  /// Đồng bộ chi tiết điểm danh từ collection sessions theo khoảng thời gian được chọn
  Future<AttendanceSummary> getAttendanceSummary({
    required String studentId,
    String? classId,
    String period = 'Học kỳ 1', // 'Cả năm', 'Học kỳ 1', 'Học kỳ 2', 'Tháng này'
  }) async {
    try {
      final classIds = (classId != null && classId.isNotEmpty) ? [classId] : <String>[];
      final docs = await _fetchSessionDocs(classIds);
      final now = DateTime.now();

      DateTime? startDate;
      DateTime? endDate;

      // Năm học hiện tại (ví dụ 2026-2027: HK1 từ 01/08 đến 31/12, HK2 từ 01/01 đến 31/05)
      final baseYear = now.month >= 8 ? now.year : now.year - 1;

      if (period == 'Tháng này') {
        startDate = DateTime(now.year, now.month, 1);
        endDate = DateTime(now.year, now.month + 1, 0, 23, 59, 59);
      } else if (period == 'Học kỳ 1') {
        startDate = DateTime(baseYear, 8, 1);
        endDate = DateTime(baseYear, 12, 31, 23, 59, 59);
      } else if (period == 'Học kỳ 2') {
        startDate = DateTime(baseYear + 1, 1, 1);
        endDate = DateTime(baseYear + 1, 5, 31, 23, 59, 59);
      } // 'Cả năm' thì để startDate và endDate = null (quét toàn bộ)

      int total = 0;
      int attended = 0;
      int unexcused = 0;
      final List<AbsenceRecord> absences = [];

      for (final doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final seat = _findSeat(data, studentId);
        if (seat == null) continue;

        final start = _parseDateTime(data['start_time']) ??
            _parseDateTime(data['session_date']);
        final end = _parseDateTime(data['end_time']);

        // Chỉ tính các buổi học đã kết thúc
        if (!_hasEnded(data, start, end, now)) continue;

        final sessionTime = start ?? end ?? now;

        // Lọc theo khoảng thời gian
        if (startDate != null && sessionTime.isBefore(startDate)) continue;
        if (endDate != null && sessionTime.isAfter(endDate)) continue;

        total++;
        final isPresent = seat['is_present'] == true;

        if (isPresent) {
          attended++;
        } else {
          unexcused++;
          final dateStr =
              '${_two(sessionTime.day)}/${_two(sessionTime.month)}/${sessionTime.year}';
          final subject = _subjectOf(doc.id, data);

          absences.add(AbsenceRecord(
            date: dateStr,
            type: 'Vắng không phép',
            reason: 'Buổi học môn $subject',
          ));
        }
      }

      absences.sort((a, b) => b.date.compareTo(a.date));

      return AttendanceSummary(
        totalSessions: total,
        attendedSessions: attended,
        excusedAbsences: 0,
        unexcusedAbsences: unexcused,
        lateSessions: 0,
        absenceList: absences,
      );
    } catch (e) {
      debugPrint('Lỗi tính attendance: $e');
      return const AttendanceSummary();
    }
  }

  Future<List<ParentNotification>> getNotificationsForStudent({
    required String studentId,
    required List<String> classIds,
  }) async {
    final ids = classIds.where((e) => e.isNotEmpty).toSet().toList();
    if (ids.isEmpty) return [];

    try {
      final docs = await _fetchSessionDocs(ids);

      final now = DateTime.now();
      final teacherCache = <String, String>{};
      final result = <ParentNotification>[];

      for (final doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};

        final seat = _findSeat(data, studentId);
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
      debugPrint('--> [Notification] Lỗi: $e');
      rethrow;
    }
  }

  Future<HomeStats> getHomeStats({
    required String studentId,
    required List<String> classIds,
  }) async {
    final ids = classIds.where((e) => e.isNotEmpty).toSet().toList();
    if (ids.isEmpty) return const HomeStats();

    try {
      final docs = await _fetchSessionDocs(ids);
      final now = DateTime.now();

      DateTime? nearestNextStart;
      int totalEnded = 0;
      int attended = 0;
      int unexcused = 0;
      double totalScore = 0.0;
      int scoreCount = 0;

      for (final doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final seat = _findSeat(data, studentId);
        if (seat == null) continue;

        final start = _parseDateTime(data['start_time']) ??
            _parseDateTime(data['session_date']);
        final end = _parseDateTime(data['end_time']);

        if (start != null && start.isAfter(now)) {
          if (nearestNextStart == null || start.isBefore(nearestNextStart)) {
            nearestNextStart = start;
          }
        }

        final ended = _hasEnded(data, start, end, now);
        if (ended) {
          totalEnded++;
          final isPresent = seat['is_present'] == true;
          if (isPresent) {
            attended++;
            final score = seat['attention_score'];
            if (score is num && score > 0) {
              totalScore += score.toDouble();
              scoreCount++;
            }
          } else {
            unexcused++;
          }
        }
      }

      String nextTimeStr = '--:--';
      if (nearestNextStart != null) {
        final isToday = nearestNextStart.year == now.year &&
            nearestNextStart.month == now.month &&
            nearestNextStart.day == now.day;
        final timePart =
            '${_two(nearestNextStart.hour)}:${_two(nearestNextStart.minute)}';
        nextTimeStr = isToday ? timePart : 'T${nearestNextStart.weekday} $timePart';
      }

      int notiCount = 0;
      try {
        final notifications = await getNotificationsForStudent(
          studentId: studentId,
          classIds: ids,
        );
        notiCount = notifications.length;
      } catch (_) {}

      final double avgScore =
          scoreCount > 0 ? (totalScore / scoreCount) : 0.0;

      return HomeStats(
        nextSessionTime: nextTimeStr,
        avgAttention: avgScore,
        totalEnded: totalEnded,
        attended: attended,
        unexcusedAbsence: unexcused,
        excusedAbsence: 0,
        lateCount: 0,
        notificationCount: notiCount,
      );
    } catch (e) {
      debugPrint('--> [HomeStats] Lỗi: $e');
      return const HomeStats();
    }
  }

  /// Lấy thống kê mức độ tập trung theo môn và điểm danh cho màn hình Tổng quan
  Future<OverviewStats> getOverviewStats({
    required String studentId,
    required List<String> classIds,
    required String period, // 'Hôm nay', 'Tuần này', 'Tháng này'
  }) async {
    final ids = classIds.where((e) => e.isNotEmpty).toSet().toList();
    if (ids.isEmpty) return const OverviewStats();

    try {
      final docs = await _fetchSessionDocs(ids);
      final now = DateTime.now();

      DateTime startDate;
      if (period == 'Hôm nay') {
        startDate = DateTime(now.year, now.month, now.day);
      } else if (period == 'Tuần này') {
        startDate = DateTime(now.year, now.month, now.day - (now.weekday - 1));
      } else {
        // Tháng này
        startDate = DateTime(now.year, now.month, 1);
      }

      int total = 0;
      int attended = 0;
      int unexcused = 0;

      final Map<String, List<double>> subjectScores = {};

      for (final doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final seat = _findSeat(data, studentId);
        if (seat == null) continue;

        final start = _parseDateTime(data['start_time']) ??
            _parseDateTime(data['session_date']);
        final end = _parseDateTime(data['end_time']);

        if (!_hasEnded(data, start, end, now)) continue;

        final sessionTime = start ?? end ?? now;
        if (sessionTime.isBefore(startDate)) continue;

        total++;
        final isPresent = seat['is_present'] == true;
        final subject = _subjectOf(doc.id, data);

        if (isPresent) {
          attended++;
          final score = seat['attention_score'];
          // Chấp nhận mọi giá trị số kể cả 0 để hiển thị thanh môn học
          if (score is num) {
            subjectScores.putIfAbsent(subject, () => []).add(score.toDouble());
          }
        } else {
          unexcused++;
        }
      }

      final List<SubjectFocus> subjectsList = [];
      subjectScores.forEach((subj, scores) {
        final avg = scores.isNotEmpty
            ? scores.reduce((a, b) => a + b) / scores.length
            : 0.0;
        subjectsList.add(
          SubjectFocus(
            subject: subj,
            percent: avg.round().clamp(0, 100),
          ),
        );
      });

      subjectsList.sort((a, b) => a.subject.compareTo(b.subject));

      return OverviewStats(
        subjects: subjectsList,
        totalSessions: total,
        attendedSessions: attended,
        excusedAbsences: 0,
        unexcusedAbsences: unexcused,
      );
    } catch (e) {
      debugPrint('--> [OverviewStats] Lỗi tính toán: $e');
      return const OverviewStats();
    }
  }

  Future<List<StudentSession>> getSessionsForStudent({
    required String studentId,
    required List<ChildClass> classes,
  }) async {
    final classNames = {for (final c in classes) c.id: c.name};
    final classTeachers = {for (final c in classes) c.id: c.teacherName};
    final ids = classNames.keys.where((e) => e.isNotEmpty).toList();
    if (ids.isEmpty) return [];

    try {
      final docs = await _fetchSessionDocs(ids);
      final teacherCache = <String, String>{};
      final result = <StudentSession>[];

      for (final doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final seat = _findSeat(data, studentId);
        if (seat == null) continue;

        final period = _toInt(data['period']);
        if (period == null || period < 1) continue;

        final sessionDate = _parseDateTime(data['session_date']);
        final start = _parseDateTime(data['start_time'], base: sessionDate);
        final end = _parseDateTime(data['end_time'], base: sessionDate ?? start);
        final day = start ?? sessionDate ?? end;
        if (day == null) continue;

        final classId = (data['class_id'] ?? '').toString();
        var teacherName = await _teacherName(
          (data['teacher_id'] ?? '').toString(),
          teacherCache,
        );
        if (teacherName.isEmpty) teacherName = classTeachers[classId] ?? '';

        result.add(
          StudentSession(
            id: doc.id,
            classId: classId,
            className: classNames[classId] ?? '',
            date: DateTime(day.year, day.month, day.day),
            startTime: start,
            endTime: end,
            period: period,
            subject: _subjectOf(doc.id, data),
            room: (data['room'] ?? '').toString(),
            teacherName: teacherName,
            isPresent: seat['is_present'] == true,
            attentionScore: seat['attention_score'] is num
                ? (seat['attention_score'] as num).toDouble()
                : null,
            statusEnded: _endedStatuses.contains(
              (data['status'] ?? '').toString().toLowerCase(),
            ),
          ),
        );
      }
      return result;
    } catch (e) {
      debugPrint('--> [Schedule] Lỗi: $e');
      rethrow;
    }
  }

  Future<List<DocumentSnapshot>> _fetchSessionDocs(List<String> classIds) async {
    final docs = <DocumentSnapshot>[];
    final col = _db.collection('sessions');
    for (var i = 0; i < classIds.length; i += 30) {
      final end = i + 30 > classIds.length ? classIds.length : i + 30;
      final chunk = classIds.sublist(i, end);
      final snap = chunk.length == 1
          ? await col.where('class_id', isEqualTo: chunk.first).get()
          : await col.where('class_id', whereIn: chunk).get();
      docs.addAll(snap.docs);
    }
    return docs;
  }

  Map? _findSeat(Map<String, dynamic> data, String studentId) {
    Map? scan(dynamic raw) {
      if (raw is! Map) return null;
      for (final v in raw.values) {
        if (v is Map && v['student_id']?.toString() == studentId) return v;
      }
      return null;
    }

    const knownKeys = [
      'monitored_students',
      'mnoitored_student',
      'monitored_student',
      'mnoitored_students',
    ];
    for (final key in knownKeys) {
      final seat = scan(data[key]);
      if (seat != null) return seat;
    }
    for (final raw in data.values) {
      final seat = scan(raw);
      if (seat != null) return seat;
    }
    return null;
  }

  static const _endedStatuses = ['completed', 'ended', 'finished', 'done', 'closed'];

  bool _hasEnded(
    Map<String, dynamic> data,
    DateTime? start,
    DateTime? end,
    DateTime now,
  ) {
    if (end != null) return !end.isAfter(now);
    final status = (data['status'] ?? '').toString().toLowerCase();
    if (_endedStatuses.contains(status)) {
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

  DateTime? _toDate(dynamic v) => _parseDateTime(v);

  int? _toInt(dynamic v) {
    if (v is num) return v.toInt();
    if (v is String) return int.tryParse(v.trim());
    return null;
  }

  String _two(int v) => v.toString().padLeft(2, '0');

  DateTime? _parseDateTime(dynamic v, {DateTime? base}) {
    if (v is Timestamp) return v.toDate();
    if (v is DateTime) return v;
    if (v is String) {
      final s = v.trim();
      final hm = RegExp(r'^(\d{1,2}):(\d{2})(?::\d{2})?$').firstMatch(s);
      if (hm != null) {
        if (base == null) return null;
        return DateTime(
          base.year,
          base.month,
          base.day,
          int.parse(hm.group(1)!),
          int.parse(hm.group(2)!),
        );
      }
      final dmy = RegExp(r'^(\d{1,2})/(\d{1,2})/(\d{4})$').firstMatch(s);
      if (dmy != null) {
        return DateTime(
          int.parse(dmy.group(3)!),
          int.parse(dmy.group(2)!),
          int.parse(dmy.group(1)!),
        );
      }
      return DateTime.tryParse(s);
    }
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