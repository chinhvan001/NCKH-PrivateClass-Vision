import 'package:cloud_firestore/cloud_firestore.dart';

class ParentModel {
  final String uid;
  final String name;
  final String email;
  final String phoneNumber;
  final bool isActive;

  const ParentModel({
    required this.uid,
    required this.name,
    required this.email,
    required this.phoneNumber,
    this.isActive = true,
  });

  /// Khởi tạo từ document trong collection 'parents' (doc id = uid Firebase Auth)
  factory ParentModel.fromFirestore(DocumentSnapshot<Map<String, dynamic>> doc) {
    final data = doc.data() ?? {};
    return ParentModel(
      uid: doc.id,
      name: data['name'] ?? 'Chưa cập nhật',
      email: data['email'] ?? 'Chưa cập nhật',
      phoneNumber: data['phone_number'] ?? 'Chưa cập nhật',
      isActive: data['is_active'] != false,
    );
  }
}

/// Một lớp mà học sinh đang theo học (lấy qua enrollments -> classes -> teachers)
class ChildClass {
  final String id;
  final String name;
  final String schoolYear;
  final String teacherName;

  const ChildClass({
    required this.id,
    required this.name,
    this.schoolYear = '',
    this.teacherName = '',
  });
}

/// Học sinh được liên kết với phụ huynh qua students.parent_id (hoặc parent_email)
class LinkedChild {
  final String id;
  final String name;
  final String birthday;
  final String gender;
  final List<ChildClass> classes;

  const LinkedChild({
    required this.id,
    required this.name,
    this.birthday = '',
    this.gender = '',
    this.classes = const [],
  });

  /// Tên gọi ngắn (từ cuối của họ tên), dùng trong câu thông báo
  String get shortName {
    final parts = name.trim().split(' ');
    return parts.isEmpty ? name : parts.last;
  }

  /// Ví dụ: "12A1 · Năm học 2026-2027" hoặc "12A1, 10B2"
  String get classDisplay {
    if (classes.isEmpty) return 'Chưa xếp lớp';
    if (classes.length == 1) {
      final c = classes.first;
      return c.schoolYear.isNotEmpty ? '${c.name} · Năm học ${c.schoolYear}' : c.name;
    }
    return classes.map((c) => c.name).join(', ');
  }

  /// Danh sách giáo viên phụ trách các lớp của con (không trùng lặp)
  String get teacherDisplay {
    final names = classes
        .map((c) => c.teacherName)
        .where((n) => n.isNotEmpty)
        .toSet();
    return names.isEmpty ? 'Chưa cập nhật' : names.join(', ');
  }
}
