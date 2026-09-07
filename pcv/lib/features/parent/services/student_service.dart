import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/student_model.dart';

class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy thông tin học sinh theo studentId.
  Future<StudentModel?> getStudentById(String studentId) async {
    try {
      final doc = await _db.collection('students').doc(studentId).get();
      if (!doc.exists) return null;
      return StudentModel.fromFirestore(doc);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông tin học sinh: ${e.message}');
    }
  }

  /// Stream realtime thông tin học sinh.
  Stream<StudentModel?> watchStudentById(String studentId) {
    return _db
        .collection('students')
        .doc(studentId)
        .snapshots()
        .map((doc) => doc.exists ? StudentModel.fromFirestore(doc) : null);
  }

  // ── Seed data (dùng 1 lần để tạo dữ liệu mẫu trên Firestore) ──────────────
  Future<void> seedSampleData() async {
    await _db.collection('students').doc('student_minh_anh').set({
      'name': 'Minh Anh',
      'className': 'Lớp 5A',
      'schoolName': 'Trường Tiểu học ABC',
      'teacherName': 'Nguyễn Văn A',
      'dateOfBirth': '12/03/2013',
      'parentPhone': '0987 654 321',
      'parentEmail': 'parent@gmail.com',
      'avgFocusPercent': 78,
      'totalSessions': 10,
      'presentSessions': 9,
      'excusedSessions': 0,
      'absentSessions': 0,
      'lateSessions': 1,
      'nextSessionTime': '15:30',
    });
  }
}
