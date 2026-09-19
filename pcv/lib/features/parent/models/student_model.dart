import 'package:cloud_firestore/cloud_firestore.dart';

class StudentModel {
  final String id;
  final String name;
  final String birthday;
  final bool gender; // true = nam, false = nữ
  final String parentEmail;
  final String parentId;

  const StudentModel({
    required this.id,
    required this.name,
    required this.birthday,
    required this.gender,
    required this.parentEmail,
    required this.parentId,
  });

  factory StudentModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return StudentModel(
      id: doc.id,
      name: d['name'] as String? ?? '',
      birthday: d['birthday']?.toString() ?? '',
      gender: d['gender'] as bool? ?? true,
      parentEmail: d['parent_email'] as String? ?? '',
      parentId: d['parent_id'] as String? ?? '',
    );
  }

  String get genderLabel => gender ? 'Nam' : 'Nữ';
}
