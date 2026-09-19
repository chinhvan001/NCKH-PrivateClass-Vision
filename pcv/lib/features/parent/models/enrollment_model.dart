import 'package:cloud_firestore/cloud_firestore.dart';

class EnrollmentModel {
  final String id;
  final String studentId;
  final String classId;
  final int row;
  final int column;

  const EnrollmentModel({
    required this.id,
    required this.studentId,
    required this.classId,
    required this.row,
    required this.column,
  });

  factory EnrollmentModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return EnrollmentModel(
      id: doc.id,
      studentId: d['student_id'] as String? ?? '',
      classId: d['class_id'] as String? ?? '',
      row: (d['row'] as num?)?.toInt() ?? 0,
      column: (d['column'] as num?)?.toInt() ?? 0,
    );
  }
}
