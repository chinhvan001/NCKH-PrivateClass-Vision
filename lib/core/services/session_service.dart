// File: lib/core/services/session_service.dart
import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/session_model.dart';

class SessionService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách monitoring_session kết hợp với classes trong khoảng thời gian (Future)
  Future<List<SessionModel>> getSessionsByTimeRange(
    String teacherId,
    DateTime? startDate,
    DateTime? endDate,
  ) async {
    try {
      Query query = _db.collection('monitoring_sessions');

      if (teacherId.isNotEmpty) {
        query = query.where('teacher_id', isEqualTo: teacherId);
      }

      if (startDate != null && endDate != null) {
        query = query
            .where(
              'start_time',
              isGreaterThanOrEqualTo: Timestamp.fromDate(startDate),
            )
            .where(
              'start_time',
              isLessThanOrEqualTo: Timestamp.fromDate(endDate),
            );
      }

      final querySnapshot = await query.get();

      if (querySnapshot.docs.isEmpty) {
        return [];
      }

      // Lấy danh sách class_id duy nhất để query thông tin lớp học
      final Set<String> classIds = {};
      for (var doc in querySnapshot.docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final String? cId = data['class_id'];
        if (cId != null && cId.isNotEmpty) {
          classIds.add(cId);
        }
      }

      // Lấy thông tin metadata các lớp học
      final Map<String, Map<String, dynamic>> classInfoMap = {};
      final List<String> classIdList = classIds.toList();

      for (var i = 0; i < classIdList.length; i += 30) {
        final chunk = classIdList.sublist(
          i,
          i + 30 > classIdList.length ? classIdList.length : i + 30,
        );

        final classesSnap = await _db
            .collection('classes')
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in classesSnap.docs) {
          classInfoMap[doc.id] = doc.data();
        }
      }

      List<SessionModel> result = [];
      for (var doc in querySnapshot.docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final String classId = data['class_id'] ?? '';
        final classData = classInfoMap[classId];

        final String className = classData?['class_name'] ?? 'Lớp học';
        final int classSize = (classData?['class_size'] as num?)?.toInt() ?? 0;

        result.add(
          SessionModel.fromFirestore(
            doc,
            className: className,
            classSize: classSize,
          ),
        );
      }

      // Sắp xếp theo start_time tăng dần
      result.sort((a, b) => a.start.compareTo(b.start));
      return result;
    } catch (e) {
      // In log lỗi nếu có
      // ignore: avoid_print
      print('Lỗi SessionService.getSessionsByTimeRange: $e');
      return [];
    }
  }

  /// Stream danh sách monitoring_sessions theo teacherId và khoảng thời gian (Realtime)
  Stream<List<SessionModel>> getSessionsStreamByTimeRange(
    String teacherId,
    DateTime? startDate,
    DateTime? endDate,
  ) {
    Query query = _db.collection('monitoring_sessions');

    if (teacherId.isNotEmpty) {
      query = query.where('teacher_id', isEqualTo: teacherId);
    }

    if (startDate != null && endDate != null) {
      query = query
          .where(
            'start_time',
            isGreaterThanOrEqualTo: Timestamp.fromDate(startDate),
          )
          .where(
            'start_time',
            isLessThanOrEqualTo: Timestamp.fromDate(endDate),
          );
    }

    return query.snapshots().asyncMap((querySnapshot) async {
      if (querySnapshot.docs.isEmpty) return [];

      final Set<String> classIds = {};
      for (var doc in querySnapshot.docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final String? cId = data['class_id'];
        if (cId != null && cId.isNotEmpty) {
          classIds.add(cId);
        }
      }

      final Map<String, Map<String, dynamic>> classInfoMap = {};
      final List<String> classIdList = classIds.toList();

      for (var i = 0; i < classIdList.length; i += 30) {
        final chunk = classIdList.sublist(
          i,
          i + 30 > classIdList.length ? classIdList.length : i + 30,
        );

        final classesSnap = await _db
            .collection('classes')
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in classesSnap.docs) {
          classInfoMap[doc.id] = doc.data();
        }
      }

      List<SessionModel> result = [];
      for (var doc in querySnapshot.docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final String classId = data['class_id'] ?? '';
        final classData = classInfoMap[classId];

        final String className = classData?['class_name'] ?? 'Lớp học';
        final int classSize = (classData?['class_size'] as num?)?.toInt() ?? 0;

        result.add(
          SessionModel.fromFirestore(
            doc,
            className: className,
            classSize: classSize,
          ),
        );
      }

      result.sort((a, b) => a.start.compareTo(b.start));
      return result;
    });
  }
}
