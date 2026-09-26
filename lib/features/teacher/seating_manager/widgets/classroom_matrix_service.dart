import 'package:cloud_firestore/cloud_firestore.dart';

class ClassroomMatrixService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Lấy thông tin kích thước ma trận phòng học (số hàng, số cột, tên phòng,...)
  Future<Map<String, dynamic>?> getClassroomMatrixInfo(String classroomId) async {
    // Chuyển về chữ thường để khớp với định dạng document ID trong Firestore nếu cần
    final docId = classroomId.trim().toLowerCase();
    
    final doc = await _firestore.collection('classrooms').doc(docId).get();
    
    if (doc.exists) {
      final data = doc.data()!;
      return {
        'classroom_id': doc.id,
        'classroom_name': data['classroom_name'] ?? 'Chưa cập nhật',
        'camera_name': data['camera_name'] ?? '',
        'rows': data['row_number'] ?? 5,
        'cols': data['column_number'] ?? 8, 
        'status': data['status'] ?? 'offline',
        'rtsp_url': data['rtsp_url'] ?? '',
      };
    }
    
    // Trả về giá trị mặc định phòng trường hợp không tìm thấy document phòng
    return {
      'classroom_id': classroomId,
      'classroom_name': 'Phòng học mặc định',
      'rows': 5,
      'cols': 8,
    };
  }

  // Dạng Stream nếu bạn muốn lắng nghe thay đổi thời gian thực từ phòng học
  Stream<Map<String, dynamic>?> getClassroomMatrixStream(String classroomId) {
    final docId = classroomId.trim().toLowerCase();
    return _firestore.collection('classrooms').doc(docId).snapshots().map((doc) {
      if (!doc.exists) return null;
      final data = doc.data()!;
      return {
        'classroom_id': doc.id,
        'classroom_name': data['classroom_name'] ?? '',
        'rows': data['row_number'] ?? 5,
        'cols': data['column_number'] ?? 8,
        'status': data['status'] ?? 'offline',
      };
    });
  }
}