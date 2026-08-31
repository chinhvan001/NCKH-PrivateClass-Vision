import '../models/student_model.dart';

const homeroomInfo = {
  'id': '12A1',
  'name': 'Lớp chủ nhiệm 12A1',
  'room': 'A203',
  'schedule': 'Sáng thứ 2 - 6',
  'size': 42,
};

final List<StudentModel> homeroomRoster =
    [
          'An',
          'Bảo',
          'Cường',
          'Dũng',
          'Hà',
          'Huy',
          'Khang',
          'Linh',
          'Minh',
          'Nam',
          'Ngọc',
          'Oanh',
          'Phúc',
          'Quân',
          'Sơn',
          'Trang',
          'Tú',
          'Uyên',
          'Vy',
          'Yến',
          'Bình',
          'Châu',
          'Đạt',
          'Hương',
          'Kiên',
          'Lan',
          'Mai',
          'Nhung',
          'Phong',
          'Quỳnh',
          'Sang',
          'Thảo',
          'Trí',
          'Vân',
          'Việt',
          'Xuân',
          'Ánh',
          'Diệp',
          'Hòa',
          'Long',
          'Tâm',
          'Yên',
        ]
        .asMap()
        .entries
        .map(
          (e) => StudentModel(
            id: 'HS${e.key.toString().padLeft(3, '0')}',
            name: 'Nguyễn Văn ${e.value}',
            short: e.value,
          ),
        )
        .toList();
