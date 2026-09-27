import 'package:cloud_firestore/cloud_firestore.dart';

class ClassModel {
  final String id;
  final String name;
  final String grade;
  final String room;
  final String schedule;
  final int students;
  final String classroomId;
  final String teacherId;
  final int schoolYear;

  const ClassModel({
    required this.id,
    required this.name,
    this.grade = '',
    required this.room,
    this.schedule = '',
    required this.students,
    this.classroomId = '',
    this.teacherId = '',
    this.schoolYear = 0,
  });

  /// Factory parse document from Firestore matching docs/firebase_schema.md
  factory ClassModel.fromFirestore(
    DocumentSnapshot doc, {
    String? roomName,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    final String name = (data['class_name'] ?? data['name'] ?? 'Lớp học').toString();
    final String cId = data['classroom_id']?.toString() ?? '';
    final String tId = data['teacher_id']?.toString() ?? '';
    final int size = (data['class_size'] as num?)?.toInt() ??
        (data['students'] as num?)?.toInt() ??
        0;
    final int year = (data['school_year'] as num?)?.toInt() ?? 0;
    final String gradeStr = data['grade']?.toString() ??
        (name.contains('12')
            ? 'Khối 12'
            : name.contains('11')
                ? 'Khối 11'
                : name.contains('10')
                    ? 'Khối 10'
                    : '');

    return ClassModel(
      id: doc.id,
      name: name,
      grade: gradeStr,
      room: roomName ?? (cId.isNotEmpty ? cId : 'Chưa xếp phòng'),
      schedule: data['schedule']?.toString() ?? '',
      students: size,
      classroomId: cId,
      teacherId: tId,
      schoolYear: year,
    );
  }
}

const List<ClassModel> mockClasses = [
  ClassModel(
    id: '12A1',
    name: 'Toán Đại số 12',
    grade: 'Khối 12',
    room: 'A203',
    schedule: 'T2, T4 · 08:00',
    students: 42,
  ),
  ClassModel(
    id: '12A2',
    name: 'Toán Hình học 12',
    grade: 'Khối 12',
    room: 'A204',
    schedule: 'T3, T5 · 10:00',
    students: 38,
  ),
  ClassModel(
    id: '11B1',
    name: 'Toán Đại số 11',
    grade: 'Khối 11',
    room: 'B102',
    schedule: 'T2, T6 · 14:00',
    students: 45,
  ),
  ClassModel(
    id: '10C1',
    name: 'Toán Cơ bản 10',
    grade: 'Khối 10',
    room: 'C301',
    schedule: 'T4, T7 · 08:00',
    students: 40,
  ),
];

