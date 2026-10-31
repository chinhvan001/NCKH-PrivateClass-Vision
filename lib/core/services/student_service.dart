import 'package:cloud_firestore/cloud_firestore.dart';

import '../constants/firestore_constants.dart';
import '../models/class_model.dart';
import '../models/student_model.dart';
import '../utils/firestore_parsers.dart';

class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Stream of students for a class – reads seatmap from `classes2` document
  /// and student details from `students2`.
  Stream<List<StudentModel>> getStudentsStream(String classId) {
    // Listen to the class document for seatmap changes
    return _db
        .collection(FirestoreConstants.classes)
        .doc(classId)
        .snapshots()
        .asyncMap((classSnap) async {
      if (!classSnap.exists) return <StudentModel>[];

      final classData = classSnap.data() ?? {};

      // Parse seatmap to get student_ids + positions
      final rawSeatmap = classData['seatmap'] ?? classData['seat_map'];
      final Map<String, Map<String, dynamic>> studentPositions = {};

      if (rawSeatmap is Map) {
        rawSeatmap.forEach((seatKey, seatValue) {
          if (seatValue is Map) {
            final sid = FirestoreParsers.cleanId(seatValue['student_id']);
            if (sid != null) {
              studentPositions[sid] = {
                'row': (seatValue['row'] as num?)?.toInt() ?? 0,
                'col': (seatValue['column'] as num?)?.toInt() ?? 0,
              };
            }
          }
        });
      }

      final List<String> studentIds = studentPositions.keys.toList();
      if (studentIds.isEmpty) return <StudentModel>[];

      // Fetch student details from students2 in chunks of 30
      List<StudentModel> studentList = [];

      for (var i = 0; i < studentIds.length; i += 30) {
        final chunk = studentIds.sublist(
          i,
          i + 30 > studentIds.length ? studentIds.length : i + 30,
        );

        final studentsSnap = await _db
            .collection(FirestoreConstants.students)
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in studentsSnap.docs) {
          final pos = studentPositions[doc.id] ?? {'row': 0, 'col': 0};
          studentList.add(
            StudentModel.fromFirestore(
              doc,
              row: pos['row'],
              column: pos['col'],
            ),
          );
        }
      }

      return studentList;
    });
  }
}
