import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

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
        .collection('monitoring_sessions')
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
                    .collection('classes')
                    .doc(classId)
                    .get();
                if (classDoc.exists && classDoc.data() != null) {
                  final classData = classDoc.data()!;
                  _classroomRows = (classData['rows'] as num?)?.toInt() ?? 5;
                  _classroomColumns =
                      (classData['columns'] as num?)?.toInt() ?? 8;

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

  Future<void> _fetchStudentDetails() async {
    final List<String> studentIdsToFetch = _sessionStudents
        .map((s) => s.studentId)
        .where((id) => id.isNotEmpty && !_studentDetails.containsKey(id))
        .toList();

    if (studentIdsToFetch.isEmpty) return;

    for (var i = 0; i < studentIdsToFetch.length; i += 30) {
      final chunk = studentIdsToFetch.sublist(
        i,
        i + 30 > studentIdsToFetch.length ? studentIdsToFetch.length : i + 30,
      );

      final studentsSnap = await _firestore
          .collection('students')
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

      // 2. Map lại danh sách model thành List<Map<String, dynamic>> chuẩn JSON Firestore
      final List<Map<String, dynamic>> updatedStudentsArray = _sessionStudents
          .map((s) => s.toJson())
          .toList();

      // 3. Đẩy đồng thời 2 trường lên Firestore
      await _firestore.collection('monitoring_sessions').doc(sessionId).update({
        'students': updatedStudentsArray,
        'present_student': updatedPresentCount,
      });

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
