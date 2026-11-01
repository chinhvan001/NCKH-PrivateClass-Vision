import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/parent_model.dart';

class ParentService {
  ParentService({FirebaseFirestore? db}) : _injectedDb = db;

  final FirebaseFirestore? _injectedDb;
  FirebaseFirestore get _db => _injectedDb ?? FirebaseFirestore.instance;

  Future<ParentModel?> getParent(String uid) async {
    final doc = await _db.collection('parents').doc(uid).get();
    return doc.exists ? ParentModel.fromFirestore(doc) : null;
  }

  /// Theo dõi danh sách con của phụ huynh theo sơ đồ CSDL:
  /// students.parent_id == uid, cộng thêm các học sinh chỉ mới điền parent_email
  /// (trường hợp nhà trường nhập học sinh trước khi phụ huynh đăng nhập lần đầu).
  /// Khi giáo viên/admin sửa parent_id trên Firestore, app nhận thay đổi ngay.
  Stream<List<LinkedChild>> watchChildren({required String uid, String? email}) {
    return _db
        .collection('students')
        .where('parent_id', isEqualTo: uid)
        .snapshots()
        .asyncMap((snap) async {
      final studentDocs = <String, DocumentSnapshot<Map<String, dynamic>>>{
        for (final doc in snap.docs) doc.id: doc,
      };

      if (email != null && email.isNotEmpty) {
        final byEmail = await _db
            .collection('students')
            .where('parent_email', isEqualTo: email)
            .get();
        for (final doc in byEmail.docs) {
          studentDocs.putIfAbsent(doc.id, () => doc);
        }
      }

      final children = await Future.wait(studentDocs.values.map(_buildChild));
      children.sort((a, b) => a.name.compareTo(b.name));
      return children;
    });
  }

  Future<LinkedChild> _buildChild(DocumentSnapshot<Map<String, dynamic>> studentDoc) async {
    final sData = studentDoc.data() ?? {};
    final fullName =
        (sData['student_name'] ?? sData['full_name'] ?? sData['name'] ?? 'Học sinh').toString();

    // Một học sinh có thể học nhiều lớp -> lấy tất cả enrollments của học sinh
    final enrollSnap = await _db
        .collection('enrollments')
        .where('student_id', isEqualTo: studentDoc.id)
        .get();

    final classIds = enrollSnap.docs
        .map((doc) => (doc.data()['class_id'] ?? '').toString())
        .where((id) => id.isNotEmpty)
        .toSet();

    final classes = await Future.wait(classIds.map(_fetchClass));

    return LinkedChild(
      id: studentDoc.id,
      name: fullName,
      birthday: _formatDate(sData['birthday']),
      gender: (sData['gender'] ?? '').toString(),
      classes: classes.whereType<ChildClass>().toList(),
    );
  }

  Future<ChildClass?> _fetchClass(String classId) async {
    final classDoc = await _db.collection('classes').doc(classId).get();
    final cData = classDoc.data();
    if (cData == null) return null;

    String teacherName = '';
    final teacherId = (cData['teacher_id'] ?? '').toString();
    if (teacherId.isNotEmpty) {
      final teacherDoc = await _db.collection('teachers').doc(teacherId).get();
      teacherName = (teacherDoc.data()?['name'] ?? '').toString();
    }

    return ChildClass(
      id: classDoc.id,
      name: (cData['class_name'] ?? 'Lớp $classId').toString(),
      schoolYear: (cData['school_year'] ?? '').toString(),
      teacherName: teacherName,
    );
  }

  String _formatDate(dynamic value) {
    if (value is Timestamp) {
      final d = value.toDate();
      final dd = d.day.toString().padLeft(2, '0');
      final mm = d.month.toString().padLeft(2, '0');
      return '$dd/$mm/${d.year}';
    }
    return value?.toString() ?? '';
  }
}
