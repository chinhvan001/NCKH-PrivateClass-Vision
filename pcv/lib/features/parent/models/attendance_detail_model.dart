import 'package:cloud_firestore/cloud_firestore.dart';

class AttendanceDetailModel {
  final String id;
  final String studentId;
  final String date;
  final String type; // 'present' | 'absent_excused' | 'absent' | 'late'
  final String reason;
  final String month; // VD: '05/2024'

  const AttendanceDetailModel({
    required this.id,
    required this.studentId,
    required this.date,
    required this.type,
    required this.reason,
    required this.month,
  });

  factory AttendanceDetailModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return AttendanceDetailModel(
      id: doc.id,
      studentId: d['studentId'] as String? ?? '',
      date: d['date'] as String? ?? '',
      type: d['type'] as String? ?? 'present',
      reason: d['reason'] as String? ?? '',
      month: d['month'] as String? ?? '',
    );
  }

  Map<String, dynamic> toMap() => {
        'studentId': studentId,
        'date': date,
        'type': type,
        'reason': reason,
        'month': month,
      };

  String get typeLabel {
    switch (type) {
      case 'absent_excused':
        return 'Vắng có phép';
      case 'absent':
        return 'Vắng không phép';
      case 'late':
        return 'Đi muộn';
      default:
        return 'Có mặt';
    }
  }
}
