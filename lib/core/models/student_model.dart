import 'package:cloud_firestore/cloud_firestore.dart';

import '../utils/firestore_parsers.dart';

class StudentModel {
  final String id;
  final String name;
  final String short;
  final int? row;
  final int? column;
  final String gender;
  final String birthday;
  final String parentId;
  final String parentEmail;
  final String parentName;
  final String parentPhone;
  final bool isStudying;
  final bool isActive;
  final String status;

  const StudentModel({
    required this.id,
    required this.name,
    required this.short,
    this.row,
    this.column,
    this.gender = '',
    this.birthday = '',
    this.parentId = '',
    this.parentEmail = '',
    this.parentName = '',
    this.parentPhone = '',
    this.isStudying = true,
    this.isActive = true,
    this.status = 'active',
  });

  /// Factory constructor parsing document from `students2` collection.
  factory StudentModel.fromFirestore(
    DocumentSnapshot doc, {
    int? row,
    int? column,
    bool isStudying = true,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    // Typo-safe full-name with fallback chain
    final String fullName = FirestoreParsers.string(
      data,
      ['fullname', 'full_name', 'student_name', 'name'],
      'Học sinh',
    );

    // Auto calculate short name if not provided
    final String shortName =
        data['short_name']?.toString() ??
        (fullName.trim().isNotEmpty ? fullName.trim().split(' ').last : 'HS');

    String birthdayStr = '';
    final rawBday = data['birthday'] ?? data['dob'];
    if (rawBday != null) {
      if (rawBday is Timestamp) {
        final DateTime dt = rawBday.toDate();
        birthdayStr =
            '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      } else {
        birthdayStr = rawBday.toString();
      }
    }

    return StudentModel(
      id: doc.id,
      name: fullName,
      short: shortName,
      row: row ?? (data['row'] as num?)?.toInt(),
      column: column ?? (data['column'] as num?)?.toInt(),
      gender: data['gender']?.toString() ?? 'Chưa rõ',
      birthday: birthdayStr,
      parentId: data['parent_id']?.toString() ?? '',
      parentEmail: data['parent_email']?.toString() ?? '',
      parentName: FirestoreParsers.string(data, ['parent_name']),
      parentPhone: FirestoreParsers.string(
        data,
        ['parent_phonenumber', 'parent_phone_number', 'phone_number'],
      ),
      isStudying: isStudying,
      isActive: data['is_active'] != false,
      status: data['status']?.toString() ?? 'active',
    );
  }

  /// Create copy with updated properties
  StudentModel copyWith({
    String? id,
    String? name,
    String? short,
    int? row,
    int? column,
    String? gender,
    String? birthday,
    String? parentId,
    String? parentEmail,
    String? parentName,
    String? parentPhone,
    bool? isStudying,
    bool? isActive,
    String? status,
  }) {
    return StudentModel(
      id: id ?? this.id,
      name: name ?? this.name,
      short: short ?? this.short,
      row: row ?? this.row,
      column: column ?? this.column,
      gender: gender ?? this.gender,
      birthday: birthday ?? this.birthday,
      parentId: parentId ?? this.parentId,
      parentEmail: parentEmail ?? this.parentEmail,
      parentName: parentName ?? this.parentName,
      parentPhone: parentPhone ?? this.parentPhone,
      isStudying: isStudying ?? this.isStudying,
      isActive: isActive ?? this.isActive,
      status: status ?? this.status,
    );
  }
}
