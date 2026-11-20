import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/constants/firestore_constants.dart';
import '../../../../core/models/session_model.dart';
import '../../../../core/models/session_student_model.dart';
import '../../../../core/models/student_model.dart';

class SessionDetailController extends ChangeNotifier {
  final String sessionId;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  SessionDetailController({required this.sessionId}) {
    init();
  }

  int _classroomRows = 5;
  int _classroomColumns = 8;

  int get classroomRows => _classroomRows;
  int get classroomColumns => _classroomColumns;

  bool _isLoading = true;
  String? _errorMessage;
  SessionModel? _session;
  List<SessionStudentModel> _sessionStudents = [];
  List<SessionStudentModel> _originalSessionStudents = [];
  bool _hasChanges = false;
  bool _isSaving = false;
  final Map<String, StudentModel> _studentDetails = {};
  StreamSubscription? _subscription;

  /// Track the original field name used in Firestore so saveChanges() writes
  /// back to the same field the data was read from.
  String _monitoredStudentsFieldName = 'monitored_students';

  /// Track whether the data was stored as a Map (seat_id keyed) or List.
  bool _dataIsMap = false;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  SessionModel? get session => _session;
  List<SessionStudentModel> get sessionStudents => _sessionStudents;
  bool get hasChanges => _hasChanges;
  bool get isSaving => _isSaving;

  int get totalStudents => _sessionStudents.length;
  int get presentCount => _sessionStudents.where((s) => s.isPresent).length;
  int get absentCount => _sessionStudents.where((s) => !s.isPresent).length;
  int get distractedCount =>
      _sessionStudents.where((s) => s.isPresent && !s.isAttention).length;

  void init() {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    _listenToSession();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  void _listenToSession() {
    _subscription?.cancel();
    _subscription = _firestore
        .collection(FirestoreConstants.sessions)
        .doc(sessionId)
        .snapshots()
        .listen(
          (snapshot) async {
            if (!snapshot.exists) {
              _isLoading = false;
              _errorMessage = "Không tìm thấy buổi học";
              notifyListeners();
              return;
            }

            try {
              final data = snapshot.data() ?? {};
              _session = SessionModel.fromFirestore(snapshot);

              final classId = data['class_id']?.toString() ?? '';

              if (classId.isNotEmpty) {
                final classDoc = await _firestore
                    .collection(FirestoreConstants.classes)
                    .doc(classId)
                    .get();
                if (classDoc.exists && classDoc.data() != null) {
                  final classData = classDoc.data()!;
                  _classroomRows =
                      (classData['row_count'] as num?)?.toInt() ??
                      (classData['rows'] as num?)?.toInt() ?? 5;
                  _classroomColumns =
                      (classData['column_count'] as num?)?.toInt() ??
                      (classData['columns'] as num?)?.toInt() ?? 8;

                  // Build a lookup from seat key (e.g. "S01") -> {row, column}
                  // from the class seatmap so we can resolve coordinates for
                  // monitored_students entries that use seat keys.
                  final Map<String, dynamic> classSeatmap =
                      (classData['seatmap'] is Map
                          ? Map<String, dynamic>.from(classData['seatmap'])
                          : (classData['seat_map'] is Map
                              ? Map<String, dynamic>.from(classData['seat_map'])
                              : <String, dynamic>{}));

                  final dynamic rawMonitoredStudents = data['monitored_students'] ??
                      data['mnoitored_student'] ??
                      data['monitored_student'];

                  // Detect which field name was found so we can write back correctly
                  if (data.containsKey('monitored_students')) {
                    _monitoredStudentsFieldName = 'monitored_students';
                  } else if (data.containsKey('mnoitored_student')) {
                    _monitoredStudentsFieldName = 'mnoitored_student';
                  } else if (data.containsKey('monitored_student')) {
                    _monitoredStudentsFieldName = 'monitored_student';
                  }

                  if (rawMonitoredStudents is Map) {
                    _dataIsMap = true;
                    _sessionStudents = [];
                    rawMonitoredStudents.forEach((seatKey, seatValue) {
                      if (seatValue is Map<String, dynamic>) {
                        _sessionStudents.add(
                          _parseMonitoredEntry(
                              seatKey, seatValue, classSeatmap),
                        );
                      } else if (seatValue is Map) {
                        _sessionStudents.add(
                          _parseMonitoredEntry(
                            seatKey,
                            Map<String, dynamic>.from(seatValue),
                            classSeatmap,
                          ),
                        );
                      }
                    });
                  } else {
                    _dataIsMap = false;
                    final List<dynamic> sessionStudentsList =
                        data['students'] ?? [];
                    if (sessionStudentsList.isEmpty &&
                        classData['seating_matrix'] != null) {
                      final Map<String, dynamic> matrix =
                          Map<String, dynamic>.from(classData['seating_matrix']);
                      _sessionStudents = [];
                      matrix.forEach((key, studentId) {
                        if (studentId != null &&
                            studentId.toString().isNotEmpty) {
                          final parts = key.split(',');
                          if (parts.length == 2) {
                            final r = int.tryParse(parts[0]) ?? 0;
                            final c = int.tryParse(parts[1]) ?? 0;
                            _sessionStudents.add(
                              SessionStudentModel(
                                studentId: studentId.toString(),
                                row: r,
                                column: c,
                                isPresent: true,
                                isAttention: true,
                              ),
                            );
                          }
                        }
                      });
                    } else {
                      _sessionStudents = sessionStudentsList
                          .whereType<Map<String, dynamic>>()
                          .map((e) => SessionStudentModel.fromJson(e))
                          .toList();
                    }
                  }
                  if (!_hasChanges) {
                    _originalSessionStudents = List<SessionStudentModel>.from(
                      _sessionStudents,
                    );
                  }
                }
              } else {
                final List<dynamic> studentsList = data['students'] ?? [];
                final loaded = studentsList
                    .whereType<Map<String, dynamic>>()
                    .map((e) => SessionStudentModel.fromJson(e))
                    .toList();
                if (!_hasChanges) {
                  _originalSessionStudents = List<SessionStudentModel>.from(
                    loaded,
                  );
                  _sessionStudents = loaded;
                }
              }

              await _fetchStudentDetails();

              // Filter out mock data or ghost students but retain valid entries even if student doc is pending load
              _sessionStudents.removeWhere(
                  (s) => s.studentId.trim().isEmpty);
              _originalSessionStudents.removeWhere(
                  (s) => s.studentId.trim().isEmpty);

              _isLoading = false;
              notifyListeners();
            } catch (e) {
              _isLoading = false;
              _errorMessage = "Lỗi xử lý dữ liệu: $e";
              notifyListeners();
            }
          },
          onError: (error) {
            _isLoading = false;
            _errorMessage = "Lỗi kết nối: $error";
            notifyListeners();
          },
        );
  }

  /// Parse a single monitored_students entry (keyed by seatId like "S01"),
  /// resolving row/column from the class seatmap when missing from the entry.
  SessionStudentModel _parseMonitoredEntry(
    String seatKey,
    Map<String, dynamic> entryData,
    Map<String, dynamic> classSeatmap,
  ) {
    final model = SessionStudentModel.fromMapEntry(seatKey, entryData);

    // If row/column are 0 (i.e. not stored in the monitored_students entry),
    // try to resolve them from the class seatmap using the same seat key.
    if (model.row == 0 && model.column == 0 && classSeatmap.containsKey(seatKey)) {
      final seatData = classSeatmap[seatKey];
      if (seatData is Map) {
        final seatMap = Map<String, dynamic>.from(seatData);
        final resolvedRow = (seatMap['row'] as num?)?.toInt() ?? 0;
        final resolvedCol =
            (seatMap['column'] as num?)?.toInt() ??
            (seatMap['col'] as num?)?.toInt() ?? 0;
        if (resolvedRow > 0 && resolvedCol > 0) {
          return model.copyWith(row: resolvedRow, column: resolvedCol);
        }
      }
    }

    return model;
  }

  Future<void> _fetchStudentDetails() async {
    final List<String> studentIdsToFetch = _sessionStudents
        .map((s) => s.studentId)
        .where((id) => id.trim().isNotEmpty && !_studentDetails.containsKey(id))
        .toList();

    if (studentIdsToFetch.isEmpty) return;

    for (var i = 0; i < studentIdsToFetch.length; i += 30) {
      final chunk = studentIdsToFetch.sublist(
        i,
        i + 30 > studentIdsToFetch.length ? studentIdsToFetch.length : i + 30,
      );

      final studentsSnap = await _firestore
          .collection(FirestoreConstants.students)
          .where(FieldPath.documentId, whereIn: chunk)
          .get();

      for (var doc in studentsSnap.docs) {
        _studentDetails[doc.id] = StudentModel.fromFirestore(doc);
      }
    }
  }

  StudentModel? getStudentInfo(String studentId) {
    return _studentDetails[studentId];
  }

  /// Đánh dấu tất cả học sinh là có mặt (chỉ cập nhật local, chờ saveChanges)
  void markAllPresent() {
    final updatedStudents = _sessionStudents
        .map((s) => s.copyWith(isPresent: true, isAttention: true))
        .toList();
    _sessionStudents = updatedStudents;
    _hasChanges = true;
    notifyListeners();
  }

  /// Đánh dấu tất cả học sinh là vắng mặt (chỉ cập nhật local, chờ saveChanges)
  void markAllAbsent() {
    final updatedStudents = _sessionStudents
        .map((s) => s.copyWith(isPresent: false, isAttention: false))
        .toList();
    _sessionStudents = updatedStudents;
    _hasChanges = true;
    notifyListeners();
  }

  void toggleAttendance(String studentId) {
    final index = _sessionStudents.indexWhere((s) => s.studentId == studentId);
    if (index == -1) return;

    final student = _sessionStudents[index];
    final bool currentPresent = student.isPresent;
    final bool currentAttention = student.isAttention;

    bool nextPresent = currentPresent;
    bool nextAttention = currentAttention;

    // Cycle: Present & Attention -> Present & Not Attention -> Not Present -> Present & Attention
    if (currentPresent && currentAttention) {
      nextPresent = true;
      nextAttention = false;
    } else if (currentPresent && !currentAttention) {
      nextPresent = false;
      nextAttention = false;
    } else {
      nextPresent = true;
      nextAttention = true;
    }

    updateStudentSessionData(
      studentId,
      isPresent: nextPresent,
      isAttention: nextAttention,
    );
  }

  void updateStudentSessionData(
    String studentId, {
    required bool isPresent,
    bool? isAttention,
    String? note,
  }) {
    final index = _sessionStudents.indexWhere((s) => s.studentId == studentId);
    if (index == -1) return;

    final updatedStudents = List<SessionStudentModel>.from(_sessionStudents);
    final current = updatedStudents[index];

    updatedStudents[index] = current.copyWith(
      isPresent: isPresent,
      isAttention: isAttention ?? current.isAttention,
      note: note ?? current.note,
    );

    _sessionStudents = updatedStudents;
    _hasChanges = true;
    notifyListeners();
  }

  void cancelChanges() {
    _sessionStudents = List<SessionStudentModel>.from(_originalSessionStudents);
    _hasChanges = false;
    notifyListeners();
  }

  Future<bool> saveChanges() async {
    if (_isSaving) return false;
    _isSaving = true;
    notifyListeners();

    try {
      // 1. Tính toán lại số lượng học sinh có mặt thực tế
      final int updatedPresentCount = _sessionStudents
          .where((s) => s.isPresent)
          .length;

      // 2. Build the update payload in the same format (Map or List) as the
      //    original Firestore data to avoid overwriting AI fields.
      final Map<String, dynamic> updateData = {
        'present_student': updatedPresentCount,
      };

      if (_dataIsMap) {
        // Write back as dot-notation updates to preserve the original Map
        // structure and avoid wiping other fields the AI may have set.
        for (final s in _sessionStudents) {
          final key = s.seatId.isNotEmpty ? s.seatId : 'R${s.row}C${s.column}';
          final prefix = '$_monitoredStudentsFieldName.$key';
          updateData['$prefix.is_present'] = s.isPresent;
          updateData['$prefix.is_attention'] = s.isAttention;
          updateData['$prefix.note'] = s.note;
          if (s.attentionScore != null) {
            updateData['$prefix.attention_score'] = s.attentionScore;
          }
        }
      } else {
        // Legacy List format
        final List<Map<String, dynamic>> updatedStudentsArray = _sessionStudents
            .map((s) => s.toJson())
            .toList();
        updateData['students'] = updatedStudentsArray;
      }

      // 3. Đẩy lên Firestore
      await _firestore
          .collection(FirestoreConstants.sessions)
          .doc(sessionId)
          .update(updateData);

      _originalSessionStudents = List<SessionStudentModel>.from(
        _sessionStudents,
      );
      _hasChanges = false;
      return true;
    } on FirebaseException catch (e) {
      debugPrint("FirebaseException saving session changes: ${e.message}");
      return false;
    } catch (e) {
      debugPrint("Error saving session changes: $e");
      return false;
    } finally {
      _isSaving = false;
      notifyListeners();
    }
  }
}
