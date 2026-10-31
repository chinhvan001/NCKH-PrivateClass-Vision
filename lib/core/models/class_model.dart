import 'package:cloud_firestore/cloud_firestore.dart';

import '../utils/firestore_parsers.dart';

/// A single seat-slot inside the class seatmap.
class SeatSlotModel {
  final String seatId;
  final int row;
  final int column;
  final String? studentId;
  final String status; // 'occupied' | 'empty'

  const SeatSlotModel({
    required this.seatId,
    required this.row,
    required this.column,
    this.studentId,
    this.status = 'empty',
  });

  factory SeatSlotModel.fromMap(String key, Map<String, dynamic> data) {
    final cleanSid = FirestoreParsers.cleanId(data['student_id']);
    return SeatSlotModel(
      seatId: data['seat_id']?.toString() ?? key,
      row: (data['row'] as num?)?.toInt() ?? 0,
      column: (data['column'] as num?)?.toInt() ?? 0,
      studentId: cleanSid,
      status: data['status']?.toString() ??
          (cleanSid != null ? 'occupied' : 'empty'),
    );
  }

  Map<String, dynamic> toMap() => {
        'seat_id': seatId,
        'row': row,
        'column': column,
        'student_id': studentId,
        'status': studentId != null ? 'occupied' : 'empty',
      };
}

class ClassModel {
  final String id;
  final String name;
  final String grade;
  final String room; // display name resolved from camera / classroom
  final String schedule;
  final int students; // class_size
  final String classroomId; // kept for backward compat
  final String cameraId;
  final String teacherId;
  final int schoolYear;
  final int rowCount;
  final int columnCount;
  final Map<String, SeatSlotModel> seatmap; // key = seat_id e.g. "R1C2"

  const ClassModel({
    required this.id,
    required this.name,
    this.grade = '',
    required this.room,
    this.schedule = '',
    required this.students,
    this.classroomId = '',
    this.cameraId = '',
    this.teacherId = '',
    this.schoolYear = 0,
    this.rowCount = 5,
    this.columnCount = 8,
    this.seatmap = const {},
  });

  /// Factory parse document from collection `classes2`.
  factory ClassModel.fromFirestore(DocumentSnapshot doc, {String? roomName}) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    final String name = FirestoreParsers.string(
      data,
      ['class_name', 'name'],
      'Lớp học',
    );
    final String cId = FirestoreParsers.string(data, ['classroom_id']);
    final String camId = FirestoreParsers.string(data, ['camera_id']);
    final String tId = FirestoreParsers.string(data, ['teacher_id']);
    final int size = FirestoreParsers.integer(data, ['class_size', 'students']);
    final int year = FirestoreParsers.integer(data, ['school_year']);
    final int rows = FirestoreParsers.integer(data, ['row_count', 'rows'], 5);
    final int cols =
        FirestoreParsers.integer(data, ['column_count', 'columns'], 8);

    final String gradeStr = data['grade']?.toString() ??
        (name.contains('12')
            ? 'Khối 12'
            : name.contains('11')
                ? 'Khối 11'
                : name.contains('10')
                    ? 'Khối 10'
                    : '');

    // Parse seatmap (Map<String, Map>) with typo fallback
    final Map<String, SeatSlotModel> parsedSeatmap = {};
    final rawSeatmap = data['seatmap'] ?? data['seat_map'];
    if (rawSeatmap is Map) {
      rawSeatmap.forEach((key, value) {
        if (value is Map) {
          parsedSeatmap[key.toString()] = SeatSlotModel.fromMap(
              key.toString(), Map<String, dynamic>.from(value));
        }
      });
    }

    return ClassModel(
      id: doc.id,
      name: name,
      grade: gradeStr,
      room: roomName ?? (cId.isNotEmpty ? cId : 'Chưa xếp phòng'),
      schedule: data['schedule']?.toString() ?? '',
      students: size,
      classroomId: cId,
      cameraId: camId,
      teacherId: tId,
      schoolYear: year,
      rowCount: rows,
      columnCount: cols,
      seatmap: parsedSeatmap,
    );
  }
}
