import 'package:cloud_firestore/cloud_firestore.dart';

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
  final bool isStudying;

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
    this.isStudying = true,
  });

  /// Factory constructor parsing document with null-safety protection
  factory StudentModel.fromFirestore(
    DocumentSnapshot doc, {
    int? row,
    int? column,
    bool isStudying = true,
  }) {
    final data = doc.data() as Map<String, dynamic>? ?? {};

    final String fullName = (data['student_name'] ??
            data['full_name'] ??
            data['name'] ??
            'Học sinh')
        .toString();

    // Auto calculate short name if not provided
    final String shortName = data['short_name']?.toString() ??
        (fullName.trim().isNotEmpty
            ? fullName.trim().split(' ').last
            : 'HS');

    String birthdayStr = '';
    if (data['birthday'] != null) {
      if (data['birthday'] is Timestamp) {
        final DateTime dt = (data['birthday'] as Timestamp).toDate();
        birthdayStr =
            '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      } else {
        birthdayStr = data['birthday'].toString();
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
      isStudying: isStudying,
    );
  }

  /// Create copy with updated enrollment properties
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
    bool? isStudying,
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
      isStudying: isStudying ?? this.isStudying,
    );
  }
}

