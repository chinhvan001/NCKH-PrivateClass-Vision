import 'package:cloud_firestore/cloud_firestore.dart';

class ParentModel {
  final String id;
  final String name;
  final String email;
  final String phoneNumber;
  final bool isActive;
  final Timestamp createDate;

  const ParentModel({
    required this.id,
    required this.name,
    required this.email,
    required this.phoneNumber,
    required this.isActive,
    required this.createDate,
  });

  factory ParentModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return ParentModel(
      id: doc.id,
      name: d['name'] as String? ?? '',
      email: d['email'] as String? ?? '',
      phoneNumber: d['phone_number'] as String? ?? '',
      isActive: d['is_active'] as bool? ?? true,
      createDate: d['create_date'] as Timestamp? ?? Timestamp.now(),
    );
  }
}
