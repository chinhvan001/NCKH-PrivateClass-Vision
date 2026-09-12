import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/child_model.dart';

class ChildService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách con theo parentId.
  Future<List<ChildModel>> getChildrenByParent(String parentId) async {
    try {
      final snapshot = await _db
          .collection('children')
          .where('parentId', isEqualTo: parentId)
          .get();
      return snapshot.docs.map(ChildModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải danh sách con: ${e.message}');
    }
  }

  /// Stream realtime danh sách con.
  Stream<List<ChildModel>> watchChildrenByParent(String parentId) {
    return _db
        .collection('children')
        .where('parentId', isEqualTo: parentId)
        .snapshots()
        .map((snap) => snap.docs.map(ChildModel.fromFirestore).toList());
  }

  // ── Seed data ──────────────────────────────────────────────────────────────
  Future<void> seedSampleData(String parentId) async {
    final batch = _db.batch();
    final samples = [
      {
        'parentId': parentId,
        'name': 'Minh Anh',
        'className': 'Lớp 5A',
        'schoolName': 'Trường Tiểu học ABC',
        'avgFocusPercent': 78,
      },
      {
        'parentId': parentId,
        'name': 'Gia Hưng',
        'className': 'Lớp 2B',
        'schoolName': 'Trường Tiểu học ABC',
        'avgFocusPercent': 85,
      },
    ];
    for (final data in samples) {
      final ref = _db.collection('children').doc();
      batch.set(ref, data);
    }
    await batch.commit();
  }
}
