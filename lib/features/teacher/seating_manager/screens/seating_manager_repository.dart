import 'package:cloud_firestore/cloud_firestore.dart';

import 'seat_models.dart';
import 'seating_save_validator.dart';

/// Ném ra khi giáo viên hiện tại không phải chủ sở hữu (`teacher_id`) của
/// lớp đang mở. Chỉ là lớp bảo vệ ở tầng ứng dụng, Firestore Security Rules
/// trên `classes2`/`students2` vẫn PHẢI tự kiểm tra teacher_id.
class ClassAccessDeniedException implements Exception {
  const ClassAccessDeniedException(this.classId);

  final String classId;

  @override
  String toString() => 'Không có quyền truy cập lớp học "$classId".';
}

/// Ném ra khi giáo viên không là `teacher_id` của lớp nào trong `classes2`.
class NoClassFoundException implements Exception {
  const NoClassFoundException();

  @override
  String toString() => 'Không tìm thấy lớp học nào của giáo viên này.';
}

/// Thông tin lớp: kích thước ma trận lấy từ `classes2.row_count/column_count`.
class ClassInfo {
  const ClassInfo({
    required this.className,
    required this.roomName,
    required this.rows,
    required this.cols,
  });

  final String className;
  final String roomName;
  final int rows;
  final int cols;

  static const fallback = ClassInfo(
    className: 'Lớp học',
    roomName: 'Chưa cập nhật',
    rows: 5,
    cols: 8,
  );
}

/// Toàn bộ dữ liệu màn hình cần, phát ra mỗi khi document lớp thay đổi.
class ClassSeatData {
  const ClassSeatData({
    required this.info,
    required this.entries,
    required this.roster,
    required this.lockedCells,
  });

  final ClassInfo info;

  /// Các ghế có student_id trong seat_map.
  final List<SeatEntry> entries;

  /// Roster = các student_id xuất hiện trong seat_map (sắp theo id), kèm tên
  /// lấy từ `students2`.
  final List<SeatStudent> roster;

  /// Chỉ số ô (theo hàng, từ 0) của các ghế có `status == "locked"`.
  /// Ghế khóa không xếp được học sinh và được giữ nguyên khi lưu.
  final Set<int> lockedCells;
}

/// Gom toàn bộ thao tác Firestore của màn hình Sơ đồ chỗ ngồi.
class SeatingManagerRepository {
  SeatingManagerRepository();

  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Cache họ tên theo student_id để không đọc lại students2 mỗi lần snapshot.
  final Map<String, String?> _nameCache = {};

  DocumentReference<Map<String, dynamic>> _classRef(String classId) =>
      _firestore.collection('classes2').doc(classId);

  Future<String> findClassIdByTeacher(String teacherId) async {
    final snap = await _firestore
        .collection('classes2')
        .where('teacher_id', isEqualTo: teacherId)
        .get();

    if (snap.docs.isEmpty) throw const NoClassFoundException();

    final ids = snap.docs.map((d) => d.id).toList()..sort();
    return ids.first;
  }

  /// Stream dữ liệu lớp + sơ đồ. [teacherId] PHẢI khớp `teacher_id`, nếu không
  /// stream báo [ClassAccessDeniedException].
  Stream<ClassSeatData> classSeatStream(
    String classId, {
    required String teacherId,
  }) {
    return _classRef(classId)
        .snapshots()
        .asyncMap((doc) => _resolve(doc, teacherId));
  }

  Future<ClassSeatData> _resolve(
    DocumentSnapshot<Map<String, dynamic>> doc,
    String teacherId,
  ) async {
    final data = doc.data();
    if (!doc.exists || data == null) {
      return const ClassSeatData(
        info: ClassInfo.fallback,
        entries: [],
        roster: [],
        lockedCells: {},
      );
    }

    // Thiếu teacher_id -> mặc định TỪ CHỐI.
    final classTeacherId = data['teacher_id'] as String?;
    if (classTeacherId == null || classTeacherId != teacherId) {
      throw ClassAccessDeniedException(doc.id);
    }

    final info = ClassInfo(
      className: (data['class_name'] ?? 'Lớp học').toString(),
      roomName: (data['room'] ?? 'Chưa cập nhật').toString(),
      rows: _asInt(data['row_count']) ?? ClassInfo.fallback.rows,
      cols: _asInt(data['column_count']) ?? ClassInfo.fallback.cols,
    );

    final entries = _parseSeatMap(data['seat_map']);
    final ids = entries.map((e) => e.studentId).toSet().toList()..sort();
    await _loadNames(ids);

    final roster = [
      for (final id in ids) SeatStudent.fromName(id, _nameCache[id]),
    ];
    return ClassSeatData(
      info: info,
      entries: entries,
      roster: roster,
      lockedCells: _parseLocked(data['seat_map'], info.rows, info.cols),
    );
  }

  List<SeatEntry> _parseSeatMap(dynamic raw) {
    if (raw is! Map) return const [];
    final entries = <SeatEntry>[];
    for (final value in raw.values) {
      if (value is! Map) continue;
      final studentId = value['student_id'];
      // Dữ liệu cũ có thể lưu chuỗi "null" thay vì null thật -> bỏ qua.
      if (studentId is! String || studentId.isEmpty || studentId == 'null') {
        continue;
      }
      if (value['status'] == 'locked') continue;
      entries.add(
        SeatEntry(
          studentId: studentId,
          row: _asInt(value['row']) ?? 0,
          column: _asInt(value['column']) ?? 0,
        ),
      );
    }
    return entries;
  }

  Set<int> _parseLocked(dynamic raw, int rows, int cols) {
    if (raw is! Map) return {};
    final locked = <int>{};
    for (final value in raw.values) {
      if (value is! Map || value['status'] != 'locked') continue;
      final r = _asInt(value['row']) ?? 0;
      final c = _asInt(value['column']) ?? 0;
      if (r < 1 || c < 1 || r > rows || c > cols) continue;
      locked.add((r - 1) * cols + (c - 1));
    }
    return locked;
  }

  Future<void> _loadNames(List<String> ids) async {
    final missing = ids.where((id) => !_nameCache.containsKey(id)).toList();
    // whereIn tối đa 30 giá trị mỗi truy vấn.
    for (var i = 0; i < missing.length; i += 30) {
      final chunk = missing.sublist(
        i,
        i + 30 > missing.length ? missing.length : i + 30,
      );
      final snap = await _firestore
          .collection('students2')
          .where(FieldPath.documentId, whereIn: chunk)
          .get();
      for (final d in snap.docs) {
        _nameCache[d.id] = d.data()['full_name'] as String?;
      }
      for (final id in chunk) {
        _nameCache.putIfAbsent(id, () => null); // không có doc -> hiện id
      }
    }
  }

  int? _asInt(dynamic value) => value is num ? value.toInt() : null;

  /// Lưu sơ đồ: ghi đè toàn bộ map `seat_map` của `classes2/{classId}` trong
  /// MỘT lần ghi (nguyên tử, không cần batch). Mỗi ô là một ghế
  /// (S01, S02, ...); ô trống có student_id = null, status = 'empty'.
  Future<void> saveSeats({
    required String classId,
    required List<String?> draftSeats,
    required int cols,
    required Iterable<String> requiredStudentIds,
    Set<int> lockedCells = const {},
  }) async {
    SeatingSaveValidator.ensureAllAssigned(
      draftSeats: draftSeats,
      requiredStudentIds: requiredStudentIds,
    );

    final seatMap = <String, dynamic>{};
    for (var i = 0; i < draftSeats.length; i++) {
      final seatId = seatIdForIndex(i);
      final isLocked = lockedCells.contains(i);
      final studentId = isLocked ? null : draftSeats[i];
      seatMap[seatId] = {
        'seat_id': seatId,
        'row': (i ~/ cols) + 1,
        'column': (i % cols) + 1,
        'student_id': studentId,
        'status': isLocked
            ? 'locked'
            : (studentId == null ? 'empty' : 'occupied'),
        'updated_at': FieldValue.serverTimestamp(),
      };
    }

    await _classRef(classId).update({
      'seat_map': seatMap,
      'updated_at': FieldValue.serverTimestamp(),
    });
  }
}
