import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/student_model.dart';

class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  // =========================================================================
  // CODE CŨ (SUBCOLLECTION: class/{classId}/students) - COMMENT ĐỂ DỰ PHÒNG
  // =========================================================================
  /*
  Stream<List<StudentModel>> getStudentsStream(String classId) {
    return _db
        .collection('class')
        .doc(classId)
        .collection('students')
        .snapshots()
        .map((snapshot) {
          return snapshot.docs.map((doc) {
            final data = doc.data();
            return StudentModel(
              id: data['student_id'] ?? doc.id,
              name: data['full_name'] ?? '',
              short: data['short_name'] ?? '',
            );
          }).toList();
        });
  }
  */

  // =========================================================================
  // LOGIC MỚI: QUERY THEO BẢNG TRUNG GIAN enrollments & students
  // =========================================================================
  Stream<List<StudentModel>> getStudentsStream(String classId) {
    return _db
        .collection('enrollments')
        .where('class_id', isEqualTo: classId)
        .snapshots()
        .asyncMap((enrollmentSnap) async {
      if (enrollmentSnap.docs.isEmpty) return [];

      // Map lưu tạm tọa độ theo student_id: { studentId: { 'row': 1, 'col': 1 } }
      final Map<String, Map<String, int>> seatPositions = {};
      final List<String> studentIds = [];

      for (var doc in enrollmentSnap.docs) {
        final data = doc.data();
        final String? sId = data['student_id'];
        if (sId != null && sId.isNotEmpty) {
          studentIds.add(sId);
          seatPositions[sId] = {
            'row': (data['row'] as num?)?.toInt() ?? 0,
            'col': (data['column'] as num?)?.toInt() ?? 0,
          };
        }
      }

      if (studentIds.isEmpty) return [];

      // Query lấy thông tin tên học sinh từ collection 'students'
      // Xử lý chunk 30 phần tử để tránh giới hạn whereIn của Firestore
      List<StudentModel> studentList = [];

      for (var i = 0; i < studentIds.length; i += 30) {
        final chunk = studentIds.sublist(
          i,
          i + 30 > studentIds.length ? studentIds.length : i + 30,
        );

        final studentsSnap = await _db
            .collection('students')
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in studentsSnap.docs) {
          final sData = doc.data();
          final pos = seatPositions[doc.id] ?? {'row': 0, 'col': 0};
          final fullName = (sData['student_name'] ?? sData['full_name'] ?? sData['name'] ?? 'Học sinh').toString();

          // Tự lấy từ cuối cùng làm tên ngắn (short) nếu không có trường short_name
          final shortName = sData['short_name'] ??
              (fullName.trim().isNotEmpty ? fullName.trim().split(' ').last : 'HS');

          studentList.add(
            StudentModel(
              id: doc.id,
              name: fullName,
              short: shortName,
              row: pos['row'] ?? 0,
              column: pos['col'] ?? 0,
            ),
          );
        }
      }

      return studentList;
    });
  }
}