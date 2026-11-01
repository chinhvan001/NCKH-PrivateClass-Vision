import 'package:cloud_firestore/cloud_firestore.dart';

import '../../../../core/constants/firestore_constants.dart';

class ClassroomMatrixService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Lấy thông tin kích thước ma trận phòng học từ classes2 document
  /// (row_count / column_count đã nằm trong classes2, không cần collection riêng)
  Future<Map<String, dynamic>?> getClassroomMatrixInfo(
    String classId,
  ) async {
    final doc =
        await _firestore.collection(FirestoreConstants.classes).doc(classId).get();

    if (doc.exists) {
      final data = doc.data()!;
      return {
        'classroom_id': doc.id,
        'classroom_name': data['class_name'] ?? 'Chưa cập nhật',
        'camera_name': data['camera_id'] ?? '',
        'rows': (data['row_count'] as num?)?.toInt() ??
            (data['rows'] as num?)?.toInt() ??
            5,
        'cols': (data['column_count'] as num?)?.toInt() ??
            (data['columns'] as num?)?.toInt() ??
            8,
        'status': data['status'] ?? 'offline',
      };
    }

    return {
      'classroom_id': classId,
      'classroom_name': 'Phòng học mặc định',
      'rows': 5,
      'cols': 8,
    };
  }

  /// Stream lắng nghe thay đổi từ classes2 document
  Stream<Map<String, dynamic>?> getClassroomMatrixStream(String classId) {
    return _firestore
        .collection(FirestoreConstants.classes)
        .doc(classId)
        .snapshots()
        .map((doc) {
      if (!doc.exists) return null;
      final data = doc.data()!;
      return {
        'classroom_id': doc.id,
        'classroom_name': data['class_name'] ?? '',
        'rows': (data['row_count'] as num?)?.toInt() ??
            (data['rows'] as num?)?.toInt() ??
            5,
        'cols': (data['column_count'] as num?)?.toInt() ??
            (data['columns'] as num?)?.toInt() ??
            8,
        'status': data['status'] ?? 'offline',
      };
    });
  }
}
