import 'package:cloud_firestore/cloud_firestore.dart';

class SessionModel {
  final String id;
  final String date;
  final String time;
  final String subject;
  final String room;
  final int percent;
  final String status; // 'present' | 'absent' | 'late'
  final String studentId;

  const SessionModel({
    required this.id,
    required this.date,
    required this.time,
    required this.subject,
    required this.room,
    required this.percent,
    required this.status,
    required this.studentId,
  });

  factory SessionModel.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return SessionModel(
      id: doc.id,
      date: data['date'] as String? ?? '',
      time: data['time'] as String? ?? '',
      subject: data['subject'] as String? ?? '',
      room: data['room'] as String? ?? '',
      percent: (data['percent'] as num?)?.toInt() ?? 0,
      status: data['status'] as String? ?? 'present',
      studentId: data['studentId'] as String? ?? '',
    );
  }

  Map<String, dynamic> toMap() => {
        'date': date,
        'time': time,
        'subject': subject,
        'room': room,
        'percent': percent,
        'status': status,
        'studentId': studentId,
      };

  /// Chuyển về Map<String, dynamic> để dùng với các widget cũ
  Map<String, dynamic> toDisplayMap() => {
        'date': date,
        'time': time,
        'subject': subject,
        'room': room,
        'percent': percent,
        'status': status,
      };
}
