import 'package:cloud_firestore/cloud_firestore.dart';

import '../../../../core/constants/firestore_constants.dart';

class ClassroomService {
  static final ClassroomService _instance = ClassroomService._internal();
  factory ClassroomService() => _instance;
  ClassroomService._internal();

  final Map<String, String> _roomCache = {};

  /// Lấy tổng sĩ số chính xác của lớp (gộp seatmap và class_members)
  Future<int> getClassStudentCount(String classId, Map<String, dynamic> classData) async {
    final Set<String> studentIds = {};
    
    final rawSeatmap = classData['seatmap'] ?? classData['seat_map'];
    if (rawSeatmap is Map) {
      rawSeatmap.forEach((key, value) {
        if (value is Map) {
          final sId = value['student_id']?.toString().trim();
          if (sId != null && sId.isNotEmpty && sId != 'null') {
            studentIds.add(sId);
          }
        }
      });
    }

    try {
      final membersSnap = await FirebaseFirestore.instance
          .collection(FirestoreConstants.classMembers)
          .where('class_id', isEqualTo: classId)
          .get();

      for (final doc in membersSnap.docs) {
        final sId = doc.data()['student_id']?.toString().trim();
        if (sId != null && sId.isNotEmpty && sId != 'null') {
          studentIds.add(sId);
        }
      }
    } catch (e) {
      // fallback
    }

    if (studentIds.isNotEmpty) {
      return studentIds.length;
    }

    int explicitSize = (classData['class_size'] as num?)?.toInt() ??
        (classData['students'] as num?)?.toInt() ?? 0;
    return explicitSize;
  }

  /// Lấy tên phòng từ camera_id. Nếu có trong cache thì trả về ngay.
  Future<String> getClassroomName(String? roomId) async {
    if (roomId == null || roomId.trim().isEmpty) {
      return 'Chưa cập nhật';
    }

    final cleanId = roomId.trim();

    if (_roomCache.containsKey(cleanId)) {
      return _roomCache[cleanId]!;
    }

    try {
      // Try cameras collection first (new schema)
      final camDoc = await FirebaseFirestore.instance
          .collection(FirestoreConstants.cameras)
          .doc(cleanId)
          .get();

      if (camDoc.exists && camDoc.data() != null) {
        final data = camDoc.data()!;
        final String roomName =
            data['room_name'] ?? data['classroom_name'] ?? cleanId;
        _roomCache[cleanId] = roomName;
        return roomName;
      }
    } catch (e) {
      // fallback
    }

    _roomCache[cleanId] = cleanId;
    return cleanId;
  }
}
