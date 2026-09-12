import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class SubjectFocusModel {
  final String id;
  final String studentId;
  final String subject;
  final int percent;

  /// 'today' | 'week' | 'month'
  final String period;

  const SubjectFocusModel({
    required this.id,
    required this.studentId,
    required this.subject,
    required this.percent,
    required this.period,
  });

  factory SubjectFocusModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return SubjectFocusModel(
      id: doc.id,
      studentId: d['studentId'] as String? ?? '',
      subject: d['subject'] as String? ?? '',
      percent: (d['percent'] as num?)?.toInt() ?? 0,
      period: d['period'] as String? ?? 'week',
    );
  }

  Map<String, dynamic> toMap() => {
        'studentId': studentId,
        'subject': subject,
        'percent': percent,
        'period': period,
      };

  /// Màu hiển thị theo thứ tự môn học
  static Color colorForIndex(int index) {
    const colors = [
      AppColors.primary,
      AppColors.green,
      AppColors.orange,
      AppColors.red,
      AppColors.accent,
    ];
    return colors[index % colors.length];
  }
}
