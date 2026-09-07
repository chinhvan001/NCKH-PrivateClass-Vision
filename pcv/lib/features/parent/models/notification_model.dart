import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class NotificationModel {
  final String id;
  final String type;   // 'teacher' | 'reminder' | 'report'
  final String title;
  final String body;
  final String time;
  final String tab;    // 'Thông báo' | 'Nhắc nhở'
  final String studentId;

  const NotificationModel({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.time,
    required this.tab,
    required this.studentId,
  });

  factory NotificationModel.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return NotificationModel(
      id: doc.id,
      type: data['type'] as String? ?? 'teacher',
      title: data['title'] as String? ?? '',
      body: data['body'] as String? ?? '',
      time: data['time'] as String? ?? '',
      tab: data['tab'] as String? ?? 'Thông báo',
      studentId: data['studentId'] as String? ?? '',
    );
  }

  Map<String, dynamic> toMap() => {
        'type': type,
        'title': title,
        'body': body,
        'time': time,
        'tab': tab,
        'studentId': studentId,
      };

  // Helpers cho UI
  IconData get icon {
    switch (type) {
      case 'reminder':
        return Icons.alarm;
      case 'report':
        return Icons.assignment_outlined;
      default:
        return Icons.campaign_outlined;
    }
  }

  Color get iconColor {
    switch (type) {
      case 'reminder':
        return AppColors.orange;
      case 'report':
        return AppColors.green;
      default:
        return AppColors.primary;
    }
  }

  Color get bgColor {
    switch (type) {
      case 'reminder':
        return AppColors.orangeLight;
      case 'report':
        return AppColors.greenLight;
      default:
        return AppColors.accentLight;
    }
  }

  /// Chuyển về Map<String, dynamic> để dùng với widget cũ
  Map<String, dynamic> toDisplayMap() => {
        'type': type,
        'title': title,
        'body': body,
        'time': time,
        'icon': icon,
        'iconColor': iconColor,
        'bgColor': bgColor,
        'tab': tab,
      };
}
