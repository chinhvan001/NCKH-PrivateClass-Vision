import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

import '../constants/firestore_constants.dart';

Future<void> resetStudentsStatus(String docId) async {
  final FirebaseFirestore firestore = FirebaseFirestore.instance;

  try {
    DocumentReference docRef =
        firestore.collection(FirestoreConstants.sessions).doc(docId);

    DocumentSnapshot snapshot = await docRef.get();

    if (!snapshot.exists) {
      debugPrint('Không tìm thấy document với ID: $docId');
      return;
    }

    Map<String, dynamic> data = snapshot.data() as Map<String, dynamic>;

    // Handle Map structure (mnoitored_student / monitored_student)
    final rawMonitored = data['mnoitored_student'] ?? data['monitored_student'];
    if (rawMonitored is Map) {
      final String mapKey = data.containsKey('mnoitored_student')
          ? 'mnoitored_student'
          : 'monitored_student';

      final Map<String, dynamic> updatePayload = {
        'avg_attention_score': 0,
        'present_student': 0,
      };

      rawMonitored.forEach((seatKey, seatVal) {
        if (seatVal is Map) {
          updatePayload['$mapKey.$seatKey.attention_score'] = 0;
          updatePayload['$mapKey.$seatKey.is_attention'] = false;
          updatePayload['$mapKey.$seatKey.is_present'] = false;
        }
      });

      await docRef.update(updatePayload);
      debugPrint(
        'Đã reset trạng thái Map cho tất cả học sinh trong doc [$docId]!',
      );
      return;
    }

    // Handle Legacy List structure
    List<dynamic> rawStudents = data['students'] ?? [];
    List<Map<String, dynamic>> updatedStudents = rawStudents.map((item) {
      Map<String, dynamic> studentMap = Map<String, dynamic>.from(item as Map);
      studentMap['attention_score'] = 0;
      studentMap['is_attention'] = false;
      studentMap['is_present'] = false;
      return studentMap;
    }).toList();

    await docRef.update({
      'students': updatedStudents,
      'avg_attention_score': 0,
      'present_student': 0,
    });

    debugPrint(
      'Đã reset trạng thái List cho tất cả học sinh trong doc [$docId]!',
    );
  } catch (e) {
    debugPrint('Lỗi khi cập nhật document: $e');
  }
}
