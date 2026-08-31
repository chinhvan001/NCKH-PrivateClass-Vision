class ClassModel {
  final String id, name, grade, room, schedule;
  final int students;

  const ClassModel({
    required this.id,
    required this.name,
    required this.grade,
    required this.room,
    required this.schedule,
    required this.students,
  });
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
