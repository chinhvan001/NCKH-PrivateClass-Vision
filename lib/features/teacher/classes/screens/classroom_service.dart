import 'package:cloud_firestore/cloud_firestore.dart';

class ClassroomService {
  static final ClassroomService _instance = ClassroomService._internal();
  factory ClassroomService() => _instance;
  ClassroomService._internal();

  final Map<String, String> _roomCache = {};

  /// Lấy tên phòng từ classroom_id. Nếu có trong cache thì trả về ngay.
  Future<String> getClassroomName(String? roomId) async {
    if (roomId == null || roomId.trim().isEmpty) {
      return 'Chưa cập nhật';
    }

    final cleanId = roomId.trim();

    if (_roomCache.containsKey(cleanId)) {
      return _roomCache[cleanId]!;
    }

    try {
      final doc = await FirebaseFirestore.instance
          .collection('classrooms')
          .doc(cleanId)
          .get();

      if (doc.exists && doc.data() != null) {
        final data = doc.data()!;
        final String roomName =
            data['classroom_name'] ?? data['name'] ?? cleanId;
        _roomCache[cleanId] = roomName;
        return roomName;
      }
    } catch (e) {
      // Nếu lỗi mạng hoặc truy vấn, dùng tạm ID
    }

    _roomCache[cleanId] = cleanId;
    return cleanId;
  }
}
