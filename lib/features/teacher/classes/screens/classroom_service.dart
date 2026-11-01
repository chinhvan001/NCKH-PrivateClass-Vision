import 'package:cloud_firestore/cloud_firestore.dart';

import '../../../../core/constants/firestore_constants.dart';

class ClassroomService {
  static final ClassroomService _instance = ClassroomService._internal();
  factory ClassroomService() => _instance;
  ClassroomService._internal();

  final Map<String, String> _roomCache = {};

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
            data['classroom_name'] ?? data['camera_name'] ?? data['name'] ?? cleanId;
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
