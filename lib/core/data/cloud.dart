import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

Future<void> resetStudentsStatus(String docId) async {
  final FirebaseFirestore firestore = FirebaseFirestore.instance;

  try {
    DocumentReference docRef = firestore.collection('monitoring_sessions').doc(docId);
    
    // 1. Lấy dữ liệu document hiện tại
    DocumentSnapshot snapshot = await docRef.get();

    if (!snapshot.exists) {
      debugPrint('Không tìm thấy document với ID: $docId');
      return;
    }

    Map<String, dynamic> data = snapshot.data() as Map<String, dynamic>;
    List<dynamic> rawStudents = data['students'] ?? [];

    // 2. Duyệt qua từng phần tử trong mảng students và cập nhật giá trị mới
    List<Map<String, dynamic>> updatedStudents = rawStudents.map((item) {
      Map<String, dynamic> studentMap = Map<String, dynamic>.from(item as Map);

      studentMap['attention_score'] = 0;
      studentMap['is_attention'] = false;
      studentMap['is_present'] = false;

      return studentMap;
    }).toList();

    // 3. Cập nhật lại mảng students và các chỉ số tổng quan (nếu cần)
    await docRef.update({
      'students': updatedStudents,
      'avg_attention_score': 0, // Cập nhật tổng quan về 0
      'present_student': 0,      // Cập nhật số học sinh có mặt về 0
    });

    debugPrint('Đã cập nhật trạng thái cho tất cả học sinh trong doc [$docId]!');

  } catch (e) {
    debugPrint('Lỗi khi cập nhật document: $e');
  }
}