import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_grid.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_layout_builder.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_save_validator.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/student_picker_sheet.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../../core/models/student_model.dart';
import '../widgets/seating_components.dart';
import 'seating_manager_repository.dart';

enum ManagerMode { view, edit }

/// Ném ra khi mở màn hình mà không có người dùng nào đang đăng nhập
/// (không xác định được giáo viên hiện tại để kiểm tra quyền sở hữu lớp).
class _NotLoggedInException implements Exception {
  const _NotLoggedInException();

  @override
  String toString() => 'Chưa đăng nhập';
}

class SeatingManagerScreen extends StatefulWidget {
  final String? classId;

  const SeatingManagerScreen({super.key, this.classId});

  @override
  State<SeatingManagerScreen> createState() => _SeatingManagerScreenState();
}

class _SeatingManagerScreenState extends State<SeatingManagerScreen> {
  String? _targetClassId;
  // trước: late final Stream<ClassInfo> _classInfoStream;
  Stream<ClassInfo>? _classInfoStream;
  // trước: late final Stream<List<StudentModel>> _studentsStream;
  Stream<List<StudentModel>>? _studentsStream;
  late final Future<void> _resolveFuture;

  // Kích thước ma trận phòng học - lấy động từ classrooms.row_number/column_number,
  // giá trị dưới đây chỉ là mặc định tạm dùng trước khi dữ liệu về.
  int _rows = ClassInfo.fallback.rows;
  int _cols = ClassInfo.fallback.cols;

  final SeatingManagerRepository _repository = SeatingManagerRepository();

  ManagerMode _mode = ManagerMode.view;
  bool _isSaving = false;
  String? _lastRosterSignature;
  late final String? _teacherId;

  late List<String?> _savedSeats;
  late List<String?> _draftSeats;

  @override
  void initState() {
    super.initState();
    _teacherId = FirebaseAuth.instance.currentUser?.uid;
    _savedSeats = List.filled(_rows * _cols, null);
    _draftSeats = List.filled(_rows * _cols, null);
    _resolveFuture = _resolveClass();
  }

  Future<void> _resolveClass() async {
    final teacherId = _teacherId;
    if (teacherId == null) throw const _NotLoggedInException();

    final classId =
        widget.classId ?? await _repository.findClassIdByTeacher(teacherId);

    _targetClassId = classId;
    _classInfoStream = _repository.classInfoStream(
      classId,
      teacherId: teacherId,
    );
    _studentsStream = _repository.studentsStream(classId);
  }

  // Cập nhật lại kích thước ma trận khi classrooms.row_number/column_number
  // thay đổi (hoặc lần đầu tải xong). Khi kích thước đổi, làm mới toàn bộ
  // mảng ghế và buộc khởi tạo lại sơ đồ từ enrollments.
  void _updateMatrixDimensions(int newRows, int newCols) {
    if (_rows == newRows && _cols == newCols) return;
    _rows = newRows;
    _cols = newCols;
    _savedSeats = List.filled(_rows * _cols, null);
    _draftSeats = List.filled(_rows * _cols, null);
    _lastRosterSignature = null;
  }

  // Khởi tạo sơ đồ từ tọa độ row/column lấy về từ enrollments (chỉ chạy 1 lần
  // cho mỗi kích thước ma trận - xem _isInitialized/_updateMatrixDimensions).
  void _syncSeatsFromRoster(List<StudentModel> roster) {
    if (_mode == ManagerMode.edit) return; // đang sửa thì không ghi đè
    final signature = SeatingLayoutBuilder.signature(roster);
    if (signature == _lastRosterSignature) return; // dữ liệu chưa đổi
    _lastRosterSignature = signature;

    final layout = SeatingLayoutBuilder.fromRoster(
      roster,
      rows: _rows,
      cols: _cols,
    );
    debugPrint(
      '[Seating] đã xếp ${layout.placedCount}/${roster.length} | '
      'ngoài ma trận: ${layout.outOfRangeIds.length} | '
      'trùng ô: ${layout.conflictIds.length}',
    );

    _savedSeats = List.of(layout.seats);
    _draftSeats = List.of(layout.seats);
  }

  int get _assignedCount =>
      (_mode == ManagerMode.edit ? _draftSeats : _savedSeats)
          .where((s) => s != null)
          .length;

  String _accessErrorMessage(Object? error) {
  if (error is NoClassFoundException) {
    return 'Bạn không có lớp chủ nhiệm nào cả.';
  }
  if (error is ClassAccessDeniedException) {
    return 'Bạn không có quyền truy cập lớp học này.';
  }
  if (error is _NotLoggedInException) {
    return 'Vui lòng đăng nhập để xem sơ đồ lớp.';
  }
  return 'Không tải được thông tin lớp học: $error';
}

  List<StudentModel> _unassignedStudents(List<StudentModel> allStudents) {
    final usedIds = _draftSeats.where((s) => s != null).toSet();
    return allStudents.where((s) => !usedIds.contains(s.id)).toList();
  }

  void _onTapCell(int index, List<StudentModel> roster) {
    if (_mode != ManagerMode.edit || _draftSeats[index] != null) return;
    showStudentPickerSheet(
      context,
      unassignedStudents: _unassignedStudents(roster),
      onSelect: (student) => setState(() => _draftSeats[index] = student.id),
    );
  }

  void _onSwapSeats(int fromIndex, int toIndex) {
    setState(() {
      final temp = _draftSeats[toIndex];
      _draftSeats[toIndex] = _draftSeats[fromIndex];
      _draftSeats[fromIndex] = temp;
    });
  }

  // Lưu sơ đồ: toàn bộ logic Firestore nằm trong SeatingManagerRepository.
  Future<void> _save(List<StudentModel> roster) async {
    final check = SeatingSaveValidator.validate(
      draftSeats: _draftSeats,
      roster: roster,
    );
    if (!check.canSave) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(check.message)));
      return;
    }
    setState(() => _isSaving = true);
    try {
      await _repository.saveSeats(
        classId: _targetClassId!,
        draftSeats: _draftSeats,
        cols: _cols,
        requiredStudentIds: roster.map((s) => s.id),
      );
      if (!mounted) return;
      setState(() {
        _savedSeats = List.from(_draftSeats);
        _mode = ManagerMode.view;
        _isSaving = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã lưu sơ đồ lớp thành công!')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isSaving = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Lỗi khi lưu sơ đồ: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _resolveFuture,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (snap.hasError) {
          return Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  _accessErrorMessage(snap.error),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
            ),
          );
        }
        return _buildScreen(context);
      },
    );
  }

  Widget _buildScreen(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: StreamBuilder<ClassInfo>(
        stream: _classInfoStream,
        builder: (context, classSnapshot) {
          if (classSnapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (classSnapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  _accessErrorMessage(classSnapshot.error),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
            );
          }

          final classInfo = classSnapshot.data ?? ClassInfo.fallback;
          _updateMatrixDimensions(classInfo.rows, classInfo.cols);

          return StreamBuilder<List<StudentModel>>(
            stream: _studentsStream,
            builder: (context, studentSnapshot) {
              if (studentSnapshot.connectionState == ConnectionState.waiting &&
                  _lastRosterSignature == null) {
                return Column(
                  children: [
                    _buildHeader(classInfo),
                    const Expanded(
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ],
                );
              }

              if (studentSnapshot.hasError) {
                return Column(
                  children: [
                    _buildHeader(classInfo),
                    Expanded(
                      child: Center(
                        child: Text(
                          'Lỗi tải dữ liệu: ${studentSnapshot.error}',
                          style: const TextStyle(color: Colors.red),
                        ),
                      ),
                    ),
                  ],
                );
              }

              final roster = studentSnapshot.data ?? [];
              _syncSeatsFromRoster(roster);

              return Column(
                children: [
                  _buildHeader(classInfo),
                  Expanded(
                    child: Transform.translate(
                      offset: const Offset(0, -16),
                      child: Container(
                        width: double.infinity,
                        decoration: const BoxDecoration(
                          color: AppColors.appBg,
                          borderRadius: BorderRadius.only(
                            topLeft: Radius.circular(24),
                            topRight: Radius.circular(24),
                          ),
                        ),
                        child: _mode == ManagerMode.edit
                            ? _buildEditMode(roster)
                            : _buildViewMode(roster, classInfo),
                      ),
                    ),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildHeader(ClassInfo classInfo) {
    final title = _mode == ManagerMode.edit
        ? 'Sắp xếp chỗ ngồi'
        : 'Quản lý sơ đồ lớp';
    final subtitle = _mode == ManagerMode.edit
        ? 'Sơ đồ ${_rows}x$_cols · ${classInfo.className}'
        : 'Phòng ${classInfo.roomName} · Lớp chủ nhiệm';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 40),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.navy, AppColors.darkBlue],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        children: [
          if (_mode == ManagerMode.edit)
            InkWell(
              onTap: () => setState(() {
                _draftSeats = List.from(_savedSeats);
                _mode = ManagerMode.view;
              }),
              child: Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.arrow_back,
                  color: Colors.white,
                  size: 20,
                ),
              ),
            ),
          if (_mode == ManagerMode.edit) const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    height: 1.2,
                  ),
                ),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEditMode(List<StudentModel> roster) {
    final validation = SeatingSaveValidator.validate(
      draftSeats: _draftSeats,
      roster: roster,
    );
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CountCard(
                  assignedCount: _assignedCount,
                  totalSize: roster.isNotEmpty
                      ? roster.length
                      : (_rows * _cols),
                ),
                if (!validation.canSave) ...[
                  const SizedBox(height: 12),
                  Text(
                    validation.message,
                    style: const TextStyle(fontSize: 13, color: Colors.red),
                  ),
                ],
                const SizedBox(height: 12),
                const Text(
                  '• Chạm ô trống: Thêm học sinh.\n• Nhấn giữ và Kéo thả: Di chuyển / Đổi chỗ.',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.muted,
                    height: 1.6,
                  ),
                ),
                const SizedBox(height: 16),
                SeatingGrid(
                  rows: _rows,
                  cols: _cols,
                  seats: _draftSeats,
                  homeroomRoster: roster,
                  isEdit: true,
                  onTapCell: (index) => _onTapCell(index, roster),
                  onSwapSeats: _onSwapSeats,
                ),
              ],
            ),
          ),
        ),
        _buildBottomButton(
          _isSaving ? 'Đang lưu...' : 'Lưu sơ đồ',
          Icons.check,
          enabled: validation.canSave,
          onPressed: () => _save(roster),
        ),
      ],
    );
  }

  Widget _buildViewMode(List<StudentModel> roster, ClassInfo classInfo) {
    final homeroomInfo = <String, Object>{
      'id': classInfo.className,
      'name': classInfo.className,
      'room': classInfo.roomName,
      'size': roster.length,
    };

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      child: Column(
        children: [
          HomeroomInfoCard(info: homeroomInfo),
          const SizedBox(height: 20),
          if (_assignedCount > 0)
            ..._buildAssignedView(roster)
          else
            ..._buildEmptyView(roster),
        ],
      ),
    );
  }

  List<Widget> _buildAssignedView(List<StudentModel> roster) {
    return [
      CountCard(
        assignedCount: _assignedCount,
        totalSize: roster.isNotEmpty ? roster.length : (_rows * _cols),
      ),
      const SizedBox(height: 16),
      SeatingGrid(
        rows: _rows,
        cols: _cols,
        seats: _savedSeats,
        homeroomRoster: roster,
        isEdit: false,
        onTapCell: (_) {},
        onSwapSeats: (_, __) {},
      ),
      const SizedBox(height: 16),
      SizedBox(
        width: double.infinity,
        height: 48,
        child: ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brand,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            elevation: 0,
          ),
          onPressed: () => setState(() {
            _draftSeats = List.from(_savedSeats);
            _mode = ManagerMode.edit;
          }),
          icon: const Icon(Icons.edit, size: 18, color: Colors.white),
          label: const Text(
            'Chỉnh sửa sơ đồ',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ),
      ),
    ];
  }

  List<Widget> _buildEmptyView(List<StudentModel> roster) {
    return [
      Card(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.hair),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
          child: Column(
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.grid_on_rounded,
                  size: 30,
                  color: AppColors.brand,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Chưa có sơ đồ lớp',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.navy,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Hệ thống đã chuẩn bị sẵn sơ đồ $_rows x$_cols với ${roster.length} học sinh. Nhấn để gán học sinh vào vị trí.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 13, color: AppColors.muted),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.brand,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 12,
                  ),
                ),
                onPressed: () => setState(() {
                  _draftSeats = List.filled(_rows * _cols, null);
                  _mode = ManagerMode.edit;
                }),
                icon: const Icon(Icons.add, size: 18, color: Colors.white),
                label: const Text(
                  'Thiết lập sơ đồ ngay',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ];
  }

  Widget _buildBottomButton(
    String label,
    IconData icon, {
    required bool enabled,
    required VoidCallback onPressed,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppColors.hair)),
      ),
      child: SizedBox(
        width: double.infinity,
        height: 48,
        child: ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brand,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            elevation: 0,
          ),
          // null khi đang lưu -> nút tự chuyển style "disabled" mặc định của ElevatedButton.
          onPressed: (_isSaving || !enabled) ? null : onPressed,
          icon: Icon(icon, size: 20, color: Colors.white),
          label: Text(
            label,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
