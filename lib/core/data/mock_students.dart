import 'dart:math';

import '../models/class_model.dart'; // Trỏ về file chứa mockClasses của bạn

// Danh sách 42 tên học sinh mẫu
const List<String> studentNames = [
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
];

// Hàm tạo danh sách học sinh ngẫu nhiên cho từng lớp
List<String> getStudentsForClass(String classId) {
  List<String> shuffled = List.of(studentNames);

  var random = Random(classId.hashCode);
  shuffled.shuffle(random);

  final classInfo = mockClasses.firstWhere(
    (c) => c.id == classId,
    orElse: () => mockClasses.first,
  );

  // Không giới hạn số lượng nữa, nếu lớp 45 học sinh, lấy đủ 45.
  if (shuffled.length < classInfo.students) {
    shuffled.addAll(List.of(studentNames));
    shuffled.shuffle(random); // Xáo trộn lại
  }

  return shuffled.take(classInfo.students).toList();
}
