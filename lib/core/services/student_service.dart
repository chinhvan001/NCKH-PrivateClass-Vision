import 'package:cloud_firestore/cloud_firestore.dart';

import '../constants/firestore_constants.dart';
import '../models/student_model.dart';
import '../utils/firestore_parsers.dart';

class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;
  static const int _whereInChunkSize = 30;

  /// Đọc seatmap từ document lớp (classes2), lấy chi tiết học sinh từ students.
  Stream<List<StudentModel>> getStudentsStream(String classId) {
    return _db
        .collection(FirestoreConstants.classes)
        .doc(classId)
        .snapshots()
        .asyncMap((classSnap) async {
      if (!classSnap.exists) return <StudentModel>[];

      final classData = classSnap.data() ?? {};
      final rawSeatmap = classData['seatmap'] ?? classData['seat_map'];
      final Map<String, Map<String, dynamic>> seatPositions = {};

      if (rawSeatmap is Map) {
        rawSeatmap.forEach((_, seatValue) {
          if (seatValue is Map) {
            final sid = FirestoreParsers.cleanId(seatValue['student_id']);
            if (sid != null) {
              seatPositions[sid] = {
                'row': (seatValue['row'] as num?)?.toInt() ?? 0,
                'col': (seatValue['column'] as num?)?.toInt() ?? 0,
              };
            }
          }
        });
      }

      if (seatPositions.isEmpty) return <StudentModel>[];

      final studentIds = seatPositions.keys.toList();
      final chunks = <List<String>>[
        for (var i = 0; i < studentIds.length; i += _whereInChunkSize)
          studentIds.sublist(
            i,
            i + _whereInChunkSize > studentIds.length
                ? studentIds.length
                : i + _whereInChunkSize,
          ),
      ];

      final chunkResults = await Future.wait(
        chunks.map(
          (chunk) => _db
              .collection(FirestoreConstants.students)
              .where(FieldPath.documentId, whereIn: chunk)
              .get(),
        ),
      );

      final studentList = <StudentModel>[];
      for (final snap in chunkResults) {
        for (final doc in snap.docs) {
          final pos = seatPositions[doc.id];
          if (pos == null) continue;
          studentList.add(
            StudentModel.fromFirestore(
              doc,
              row: pos['row'],
              column: pos['col'],
            ),
          );
        }
      }

      studentList.sort((a, b) => a.name
          .trim()
          .split(' ')
          .last
          .compareTo(b.name.trim().split(' ').last));
      return studentList;
    });
  }
}