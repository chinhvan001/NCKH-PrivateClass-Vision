import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/parent_model.dart';

class ParentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy thông tin parent theo parentId
  Future<ParentModel?> getParentById(String parentId) async {
    try {
      final doc = await _db.collection('parents').doc(parentId).get();
      if (!doc.exists) return null;
      return ParentModel.fromFirestore(doc);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông tin phụ huynh: ${e.message}');
    }
  }

  /// Stream realtime thông tin parent
  Stream<ParentModel?> watchParentById(String parentId) {
    return _db
        .collection('parents')
        .doc(parentId)
        .snapshots()
        .map((doc) => doc.exists ? ParentModel.fromFirestore(doc) : null);
  }

  /// Lấy parent theo email (dùng sau khi login)
  Future<ParentModel?> getParentByEmail(String email) async {
    try {
      final snapshot = await _db
          .collection('parents')
          .where('email', isEqualTo: email)
          .limit(1)
          .get();
      if (snapshot.docs.isEmpty) return null;
      return ParentModel.fromFirestore(snapshot.docs.first);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông tin phụ huynh: ${e.message}');
    }
  }
}
