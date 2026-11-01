import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/constants/firestore_constants.dart';
import '../../../../core/models/class_model.dart';
import '../../../../core/models/session_model.dart';
import '../../../../core/models/student_model.dart';
import '../../../../core/utils/firestore_parsers.dart';

class ClassDetailController extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final String classId;

  ClassDetailController({required this.classId}) {
    init();
  }

  bool _isLoading = true;
  String? _errorMessage;
  ClassModel? _classDetail;
  Map<String, dynamic>? _classroomData;
  Map<String, dynamic>? _teacherData;
  List<StudentModel> _students = [];
  List<SessionModel> _sessions = [];
  int _selectedTabIndex = 0;
  String _searchStudentQuery = '';

  StreamSubscription<DocumentSnapshot>? _classSubscription;
  StreamSubscription<QuerySnapshot>? _sessionsSubscription;

  bool get isLoading => _isLoading;
  bool get hasError => _errorMessage != null;
  String? get errorMessage => _errorMessage;
  bool get hasData => _classDetail != null;

  ClassModel? get classDetail => _classDetail;
  Map<String, dynamic>? get classroomData => _classroomData;
  Map<String, dynamic>? get teacherData => _teacherData;
  List<StudentModel> get students => _students;
  List<SessionModel> get sessions => _sessions;
  int get selectedTabIndex => _selectedTabIndex;
  String get searchStudentQuery => _searchStudentQuery;

  int get totalEnrolled => _students.length;
  int get activeStudentsCount => _students.where((s) => s.isStudying).length;
  int get seatedStudentsCount => _students
      .where(
        (s) =>
            (s.row != null && s.row! > 0 && s.column != null && s.column! > 0),
      )
      .length;

  int get classroomRows => _classDetail?.rowCount ?? 5;
  int get classroomColumns => _classDetail?.columnCount ?? 8;

  String get classroomName {
    return classroomData?['classroom_name']?.toString() ??
        classDetail?.room ??
        'Chưa cập nhật';
  }

  String get cameraName {
    return classroomData?['camera_name']?.toString() ??
        _classDetail?.cameraId ??
        'Chưa cấu hình';
  }

  String get cameraStatus {
    return classroomData?['camera_status']?.toString() ??
        classroomData?['status']?.toString() ??
        'online';
  }

  double get avgAttentionScore {
    if (_sessions.isEmpty) return 0.0;
    final total = _sessions.fold<double>(
      0.0,
      (acc, item) => acc + item.avgAttentionScore,
    );
    return double.parse((total / _sessions.length).toStringAsFixed(1));
  }

  List<StudentModel> get filteredStudents {
    if (_searchStudentQuery.trim().isEmpty) {
      return _students;
    }
    final query = _searchStudentQuery.trim().toLowerCase();
    return _students
        .where(
          (s) =>
              s.name.toLowerCase().contains(query) ||
              s.short.toLowerCase().contains(query),
        )
        .toList();
  }

  void init() {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    _listenToClass();
    _listenToSessions();
  }

  void setTabIndex(int index) {
    if (_selectedTabIndex != index) {
      _selectedTabIndex = index;
      notifyListeners();
    }
  }

  void setSearchQuery(String query) {
    _searchStudentQuery = query;
    notifyListeners();
  }
  void setSearchStudentQuery(String query) {
    _searchStudentQuery = query;
    notifyListeners();
  }

  void _listenToClass() {
    _classSubscription?.cancel();
    _classSubscription = _firestore
        .collection(FirestoreConstants.classes)
        .doc(classId)
        .snapshots()
        .listen(
          (snapshot) async {
            if (!snapshot.exists) {
              _errorMessage = "Không tìm thấy dữ liệu lớp học";
              _isLoading = false;
              notifyListeners();
              return;
            }

            try {
              final data = snapshot.data() ?? {};

              String? roomName;
              final String camId = FirestoreParsers.string(
                data,
                ['camera_id', 'classroom_id'],
              );
              if (camId.isNotEmpty) {
                final camDoc = await _firestore
                    .collection(FirestoreConstants.cameras)
                    .doc(camId)
                    .get();
                if (camDoc.exists && camDoc.data() != null) {
                  _classroomData = camDoc.data()!;
                  roomName = _classroomData?['classroom_name']?.toString() ??
                      _classroomData?['camera_name']?.toString();
                }
              }

              final String tId = data['teacher_id']?.toString() ?? '';
              if (tId.isNotEmpty) {
                final teacherDoc = await _firestore
                    .collection(FirestoreConstants.teachers)
                    .doc(tId)
                    .get();
                if (teacherDoc.exists && teacherDoc.data() != null) {
                  _teacherData = teacherDoc.data()!;
                }
              }

              _classDetail =
                  ClassModel.fromFirestore(snapshot, roomName: roomName);

              await _processClassSeatmap(_classDetail!);

              _isLoading = false;
              _errorMessage = null;
              notifyListeners();
            } catch (e) {
              _errorMessage = "Lỗi xử lý dữ liệu lớp: $e";
              _isLoading = false;
              notifyListeners();
            }
          },
          onError: (e) {
            _errorMessage = "Lỗi kết nối lớp học: $e";
            _isLoading = false;
            notifyListeners();
          },
        );
  }

  Future<void> _processClassSeatmap(ClassModel classModel) async {
    try {
      final seatmap = classModel.seatmap;
      final Map<String, SeatSlotModel> studentSlots = {};

      for (final slot in seatmap.values) {
        if (slot.studentId != null && slot.studentId!.isNotEmpty) {
          studentSlots[slot.studentId!] = slot;
        }
      }

      final List<String> studentIds = studentSlots.keys.toList();
      if (studentIds.isEmpty) {
        _students = [];
        return;
      }

      final List<StudentModel> fetchedStudents = [];

      for (var i = 0; i < studentIds.length; i += 30) {
        final chunk = studentIds.sublist(
          i,
          i + 30 > studentIds.length ? studentIds.length : i + 30,
        );

        final studentsSnap = await _firestore
            .collection(FirestoreConstants.students)
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in studentsSnap.docs) {
          final slot = studentSlots[doc.id];
          fetchedStudents.add(
            StudentModel.fromFirestore(
              doc,
              row: slot?.row,
              column: slot?.column,
              isStudying: true,
            ),
          );
        }
      }

      fetchedStudents.sort((a, b) => a.name.compareTo(b.name));
      _students = fetchedStudents;
      if (_sessions.isNotEmpty) {
        _sessions = _sessions
            .map((s) => s.copyWith(
                size: _classDetail?.students ?? _students.length))
            .toList();
      }
      notifyListeners();
    } catch (e) {
      debugPrint('Lỗi _processClassSeatmap: $e');
    }
  }

  void _listenToSessions() {
    _sessionsSubscription?.cancel();
    
    final currentTeacherId = FirebaseAuth.instance.currentUser?.uid ?? '';
    
    _sessionsSubscription = _firestore
        .collection(FirestoreConstants.sessions)
        .where('class_id', isEqualTo: classId)
        .where('teacher_id', isEqualTo: currentTeacherId)
        .snapshots()
        .listen(
          (snapshot) {
            final List<SessionModel> list = [];
            for (var doc in snapshot.docs) {
              list.add(
                SessionModel.fromFirestore(
                  doc,
                  className: _classDetail?.name ?? 'Lớp học',
                  classSize: _classDetail?.students ?? _students.length,
                ),
              );
            }

            list.sort((a, b) => b.date.compareTo(a.date));
            _sessions = list;
            notifyListeners();
          },
          onError: (e) {
            debugPrint('Lỗi listen sessions: $e');
          },
        );
  }

  Future<void> refresh() async {
    init();
  }

  Future<bool> updateSessionNote(String sessionId, String newNote) async {
    try {
      await _firestore
          .collection(FirestoreConstants.sessions)
          .doc(sessionId)
          .update({'note': newNote});
      return true;
    } catch (e) {
      debugPrint('Lỗi cập nhật ghi chú buổi học: $e');
      return false;
    }
  }

  @override
  void dispose() {
    _classSubscription?.cancel();
    _sessionsSubscription?.cancel();
    super.dispose();
  }
}
