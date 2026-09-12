import 'package:cloud_firestore/cloud_firestore.dart';

class ScheduleModel {
  final String id;
  final String studentId;
  final String date;       // VD: 'Thứ 2, 20/05/2024'
  final String time;       // VD: '08:00 - 09:30'
  final String subject;
  final String room;
  final String teacherName;
  final Timestamp scheduledAt; // dùng để sort

  const ScheduleModel({
    required this.id,
    required this.studentId,
    required this.date,
    required this.time,
    required this.subject,
    required this.room,
    required this.teacherName,
    required this.scheduledAt,
  });

  factory ScheduleModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return ScheduleModel(
      id: doc.id,
      studentId: d['studentId'] as String? ?? '',
      date: d['date'] as String? ?? '',
      time: d['time'] as String? ?? '',
      subject: d['subject'] as String? ?? '',
      room: d['room'] as String? ?? '',
      teacherName: d['teacherName'] as String? ?? '',
      scheduledAt: d['scheduledAt'] as Timestamp? ?? Timestamp.now(),
    );
  }

  Map<String, dynamic> toMap() => {
        'studentId': studentId,
        'date': date,
        'time': time,
        'subject': subject,
        'room': room,
        'teacherName': teacherName,
        'scheduledAt': scheduledAt,
      };
}
