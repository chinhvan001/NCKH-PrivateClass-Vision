import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/student_model.dart';
import '../models/enrollment_model.dart';

class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách học sinh theo parentId
  Future<List<StudentModel>> getStudentsByParent(String parentId) async {
    try {
      final snapshot = await _db
          .collection('students')
          .where('parent_id', isEqualTo: parentId)
          .get();
      return snapshot.docs.map(StudentModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải danh sách học sinh: ${e.message}');
    }
  }

  /// Stream realtime danh sách học sinh theo parentId
  Stream<List<StudentModel>> watchStudentsByParent(String parentId) {
    return _db
        .collection('students')
        .where('parent_id', isEqualTo: parentId)
        .snapshots()
        .map((snap) => snap.docs.map(StudentModel.fromFirestore).toList());
  }

  /// Lấy 1 học sinh theo studentId
  Future<StudentModel?> getStudentById(String studentId) async {
    try {
      final doc = await _db.collection('students').doc(studentId).get();
      if (!doc.exists) return null;
      return StudentModel.fromFirestore(doc);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông tin học sinh: ${e.message}');
    }
  }

  /// Lấy enrollment (lớp học) của học sinh
  Future<List<EnrollmentModel>> getEnrollmentsByStudent(String studentId) async {
    try {
      final snapshot = await _db
          .collection('enrollments')
          .where('student_id', isEqualTo: studentId)
          .get();
      return snapshot.docs.map(EnrollmentModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông tin lớp học: ${e.message}');
    }
  }
}
