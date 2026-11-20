import 'package:cloud_firestore/cloud_firestore.dart';

import '../../../../core/constants/firestore_constants.dart';

class ClassService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Lấy danh sách các lớp học do giáo viên hiện tại phụ trách (from classes2)
  Stream<List<Map<String, dynamic>>> getClassesByTeacherStream(
    String teacherId,
  ) {
    return _firestore
        .collection(FirestoreConstants.classes)
        .where('teacher_id', isEqualTo: teacherId)
        .snapshots()
        .map((snapshot) {
          return snapshot.docs.map((doc) {
            final data = doc.data();
            return {
              'class_id': doc.id,
              'class_name': data['class_name'] ?? '',
              'class_size': data['class_size'] ?? 0,
              'classroom_id': data['classroom_id'] ?? '',
              'camera_id': data['camera_id'] ?? '',
              'school_year': data['school_year'] ?? '',
              'teacher_id': data['teacher_id'] ?? '',
              'row_count': data['row_count'] ?? data['rows'] ?? 5,
              'column_count': data['column_count'] ?? data['columns'] ?? 8,
            };
          }).toList();
        });
  }

  // Lấy một lớp cụ thể theo classId (from classes2)
  Future<Map<String, dynamic>?> getClassDetail(String classId) async {
    final doc = await _firestore
        .collection(FirestoreConstants.classes)
        .doc(classId)
        .get();
    if (doc.exists) {
      return {'class_id': doc.id, ...doc.data()!};
    }
    return null;
  }
}
