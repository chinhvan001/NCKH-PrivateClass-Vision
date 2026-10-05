import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

import '../../../../core/models/class_model.dart';
import '../../../../core/models/session_model.dart';
import '../../../../core/models/student_model.dart';

class ClassDetailController extends ChangeNotifier {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final String classId;

  ClassDetailController({required this.classId}) {
    init();
  }

  // --- Trạng thái (State) ---
  bool _isLoading = true;
  String? _errorMessage;
  ClassModel? _classDetail;
  Map<String, dynamic>? _classroomData;
  Map<String, dynamic>? _teacherData;
  List<StudentModel> _students = [];
  List<SessionModel> _sessions = [];
  int _selectedTabIndex = 0;
  String _searchStudentQuery = '';

  // Subscriptions
  StreamSubscription<DocumentSnapshot>? _classSubscription;
  StreamSubscription<QuerySnapshot>? _enrollmentSubscription;
  StreamSubscription<QuerySnapshot>? _sessionsSubscription;

  // --- Getters ---
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

  int get classroomRows {
    final rows = (classroomData?['row'] as num?)?.toInt();
    return (rows != null && rows > 0) ? rows : 5;
  }

  int get classroomColumns {
    final cols = (classroomData?['column'] as num?)?.toInt();
    return (cols != null && cols > 0) ? cols : 8;
  }

  String get classroomName {
    return classroomData?['classroom_name']?.toString() ??
        classDetail?.room ??
        'Chưa cập nhật';
  }

  String get cameraName {
    return classroomData?['camera_name']?.toString() ?? 'Chưa cấu hình';
  }

  String get cameraStatus {
    return classroomData?['camera_status']?.toString() ?? 'Không rõ';
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
              s.short.toLowerCase().contains(query) ||
              s.parentEmail.toLowerCase().contains(query),
        )
        .toList();
  }

  void init() {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    _listenToClass();
    _listenToEnrollmentAndStudents();
    _listenToSessions();
  }

  void setTabIndex(int index) {
    if (_selectedTabIndex != index) {
      _selectedTabIndex = index;
    }
  }

  void setSearchStudentQuery(String query) {
    _searchStudentQuery = query;
    notifyListeners();
  }

  void _listenToClass() {
    _classSubscription?.cancel();
    _classSubscription = _firestore
        .collection('classes')
        .doc(classId)
        .snapshots()
        .listen(
          (snapshot) async {
            if (!snapshot.exists) {
              _isLoading = false;
              _errorMessage = 'Không tìm thấy thông tin lớp học.';
              notifyListeners();
              return;
            }

            try {
              final data = snapshot.data() ?? {};
              final String classroomId = data['classroom_id']?.toString() ?? '';
              final String teacherId = data['teacher_id']?.toString() ?? '';

              await Future.wait([
                if (classroomId.isNotEmpty) _fetchClassroom(classroomId),
                if (teacherId.isNotEmpty) _fetchTeacher(teacherId),
              ]);

              final String roomTitle =
                  _classroomData?['classroom_name']?.toString() ??
                  (classroomId.isNotEmpty ? classroomId : 'Chưa cập nhật');

              _classDetail = ClassModel.fromFirestore(
                snapshot,
                roomName: roomTitle,
              );
              _isLoading = false;
              _errorMessage = null;
              notifyListeners();
            } catch (e) {
              _isLoading = false;
              _errorMessage = 'Lỗi xử lý dữ liệu lớp: $e';
              notifyListeners();
            }
          },
          onError: (error) {
            _isLoading = false;
            _errorMessage = 'Lỗi kết nối lớp học: $error';
            notifyListeners();
          },
        );
  }

  Future<void> _fetchClassroom(String classroomId) async {
    try {
      final doc = await _firestore
          .collection('classrooms')
          .doc(classroomId)
          .get();
      if (doc.exists) {
        _classroomData = doc.data();
      }
    } catch (e) {
      debugPrint('Lỗi fetchClassroom: $e');
    }
  }

  Future<void> _fetchTeacher(String teacherId) async {
    try {
      final doc = await _firestore.collection('teacher').doc(teacherId).get();
      if (doc.exists) {
        _teacherData = doc.data();
      }
    } catch (e) {
      debugPrint('Lỗi fetchTeacher: $e');
    }
  }

  void _listenToEnrollmentAndStudents() {
    _enrollmentSubscription?.cancel();

    _enrollmentSubscription = _firestore
        .collection('Enrollment')
        .where('class_id', isEqualTo: classId)
        .snapshots()
        .listen(
          (enrollSnap) async {
            if (enrollSnap.docs.isEmpty) {
              try {
                final fallbackSnap = await _firestore
                    .collection('enrollments')
                    .where('class_id', isEqualTo: classId)
                    .get();

                if (fallbackSnap.docs.isNotEmpty) {
                  await _processEnrollmentDocs(fallbackSnap.docs);
                  return;
                }
              } catch (_) {}

              _students = [];
              notifyListeners();
              return;
            }

            await _processEnrollmentDocs(enrollSnap.docs);
          },
          onError: (e) {
            debugPrint('Lỗi listen Enrollment: $e');
          },
        );
  }

  Future<void> _processEnrollmentDocs(List<QueryDocumentSnapshot> docs) async {
    try {
      final Map<String, Map<String, dynamic>> enrollmentMeta = {};
      final List<String> studentIds = [];

      for (var doc in docs) {
        final data = doc.data() as Map<String, dynamic>? ?? {};
        final String? sId = data['student_id']?.toString();
        if (sId != null && sId.isNotEmpty) {
          studentIds.add(sId);
          enrollmentMeta[sId] = {
            'row': (data['row'] as num?)?.toInt(),
            'column': (data['column'] as num?)?.toInt(),
            'is_studying': data['is_studying'] is bool
                ? data['is_studying']
                : true,
            'school_year': (data['school_year'] as num?)?.toInt(),
          };
        }
      }

      if (studentIds.isEmpty) {
        _students = [];
        notifyListeners();
        return;
      }

      final List<StudentModel> fetchedStudents = [];

      for (var i = 0; i < studentIds.length; i += 30) {
        final chunk = studentIds.sublist(
          i,
          i + 30 > studentIds.length ? studentIds.length : i + 30,
        );

        final studentsSnap = await _firestore
            .collection('students')
            .where(FieldPath.documentId, whereIn: chunk)
            .get();

        for (var doc in studentsSnap.docs) {
          final meta = enrollmentMeta[doc.id] ?? {};
          fetchedStudents.add(
            StudentModel.fromFirestore(
              doc,
              row: meta['row'] as int?,
              column: meta['column'] as int?,
              isStudying: (meta['is_studying'] as bool?) ?? true,
            ),
          );
        }
      }

      fetchedStudents.sort((a, b) => a.name.compareTo(b.name));
      _students = fetchedStudents;
      notifyListeners();
    } catch (e) {
      debugPrint('Lỗi _processEnrollmentDocs: $e');
    }
  }

  void _listenToSessions() {
    _sessionsSubscription?.cancel();
    _sessionsSubscription = _firestore
        .collection('monitoring_sessions')
        .where('class_id', isEqualTo: classId)
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
            debugPrint('Lỗi listen monitoring_sessions: $e');
          },
        );
  }

  Future<void> refresh() async {
    init();
  }

  @override
  void dispose() {
    _classSubscription?.cancel();
    _enrollmentSubscription?.cancel();
    _sessionsSubscription?.cancel();
    super.dispose();
  }
}
