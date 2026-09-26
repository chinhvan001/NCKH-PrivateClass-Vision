import 'package:cloud_firestore/cloud_firestore.dart';

class TeacherModel {
  final String uid;
  final String name;
  final String email;
  final String phoneNumber;
  final String subject;
  final String activeRole;

  TeacherModel({
    required this.uid,
    required this.name,
    required this.email,
    required this.phoneNumber,
    required this.subject,
    this.activeRole = 'teacher',
  });

  /// Hiển thị vai trò giáo viên kèm môn học (Ví dụ: "Giáo viên Toán")
  String get roleDisplay {
    return subject.isNotEmpty ? 'Giáo viên $subject' : 'Giáo viên';
  }

  /// Khởi tạo UserModel từ document trong collection 'teachers'
  factory TeacherModel.fromFirestore(DocumentSnapshot<Map<String, dynamic>> doc) {
    final data = doc.data() ?? {};
    return TeacherModel(
      uid: doc.id,
      name: data['name'] ?? 'Chưa cập nhật',
      email: data['email'] ?? 'Chưa cập nhật',
      phoneNumber: data['phone_number'] ?? 'Chưa cập nhật',
      subject: data['subject'] ?? '',
      activeRole: 'teacher',
    );
  }

  /// Chuyển đối tượng sang Map nếu cần lưu/cập nhật lên Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'name': name,
      'email': email,
      'phone_number': phoneNumber,
      'subject': subject,
      'active_role': activeRole,
    };
  }
}