import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_grid.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_layout_builder.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_save_validator.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/student_picker_sheet.dart';

import '../../../../../core/constants/app_colors.dart';
import 'seat_models.dart';
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
  // Một stream duy nhất từ classes2: thông tin lớp + seat_map + roster.
  Stream<ClassSeatData>? _classSeatStream;
  late final Future<void> _resolveFuture;

  // Kích thước ma trận phòng học - lấy động từ classes2.row_count/column_count,
  // giá trị dưới đây chỉ là mặc định tạm dùng trước khi dữ liệu về.
  int _rows = ClassInfo.fallback.rows;
  int _cols = ClassInfo.fallback.cols;

  final SeatingManagerRepository _repository = SeatingManagerRepository();

  ManagerMode _mode = ManagerMode.view;
  bool _isSaving = false;
  String? _lastRosterSignature;
  late final String? _teacherId;

  Set<int> _lockedCells = {};
  Set<String> _rosterIds = {};

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
    _classSeatStream = _repository.classSeatStream(
      classId,
      teacherId: teacherId,
    );
  }

  // Cập nhật lại kích thước ma trận khi classes2.row_count/column_count
  // thay đổi (hoặc lần đầu tải xong). Khi kích thước đổi, làm mới toàn bộ
  // mảng ghế và buộc khởi tạo lại sơ đồ từ classes2.seat_map.
  void _updateMatrixDimensions(int newRows, int newCols) {
    if (_rows == newRows && _cols == newCols) return;
    _rows = newRows;
    _cols = newCols;
    _savedSeats = List.filled(_rows * _cols, null);
    _draftSeats = List.filled(_rows * _cols, null);
    _lastRosterSignature = null;
  }

  // Dựng lại sơ đồ từ classes2.seat_map khi dữ liệu thật sự đổi.
  void _syncSeats(ClassSeatData data) {
    if (_mode == ManagerMode.edit) return; // đang sửa thì không ghi đè
    final signature = SeatingLayoutBuilder.signature(data.entries);
    if (signature == _lastRosterSignature) return; // dữ liệu chưa đổi
    _lastRosterSignature = signature;

    final layout = SeatingLayoutBuilder.fromEntries(
      data.entries,
      rows: _rows,
      cols: _cols,
    );
    _savedSeats = List.of(layout.seats);
    _draftSeats = List.of(layout.seats);
  }

  int get _assignedCount =>
      (_mode == ManagerMode.edit ? _draftSeats : _savedSeats)
          .where((s) => s != null && _rosterIds.contains(s))
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

  List<SeatStudent> _unassignedStudents(List<SeatStudent> allStudents) {
    final usedIds = _draftSeats.where((s) => s != null).toSet();
    return allStudents.where((s) => !usedIds.contains(s.id)).toList();
  }

  void _onTapCell(int index, List<SeatStudent> roster) {
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

  // Xóa toàn bộ học sinh khỏi bản NHÁP để xếp lại từ đầu. Chưa ghi Firestore:
  // chỉ khi bấm "Lưu sơ đồ" (và đã xếp đủ học sinh) dữ liệu mới thay đổi,
  // còn nút quay lại sẽ trả về sơ đồ đã lưu.
  Future<void> _confirmClearAll() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Xóa toàn bộ sơ đồ?'),
        content: const Text(
          'Bạn có chắc muốn xóa toàn bộ học sinh khỏi sơ đồ không? '
          'Bạn cần xếp lại tất cả học sinh trước khi có thể lưu.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text(
              'Xóa toàn bộ',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _draftSeats = List.filled(_rows * _cols, null));
  }

  // Lưu sơ đồ: toàn bộ logic Firestore nằm trong SeatingManagerRepository.
  Future<void> _save(List<SeatStudent> roster) async {
    final check = SeatingSaveValidator.validate(
      draftSeats: _draftSeats,
      roster: roster,
      lockedCount: _lockedCells.length,
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
        lockedCells: _lockedCells,
      );
      if (!mounted) return;
      setState(() {
        _savedSeats = List.from(_draftSeats);
        // Báo trước chữ ký sau khi lưu để snapshot cũ không ghi đè sơ đồ.
        _lastRosterSignature =
            SeatingLayoutBuilder.signatureAfterSave(_draftSeats, _cols);
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
      body: StreamBuilder<ClassSeatData>(
        stream: _classSeatStream,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  _accessErrorMessage(snapshot.error),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
            );
          }

          final data = snapshot.data;
          if (data == null) {
            return const Center(child: CircularProgressIndicator());
          }

          final classInfo = data.info;
          final roster = data.roster;
          _rosterIds = roster.map((s) => s.id).toSet();
          _lockedCells = data.lockedCells;
          _updateMatrixDimensions(classInfo.rows, classInfo.cols);
          _syncSeats(data);

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
                  color: Colors.white.withValues(alpha: 0.1),
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
                    color: Colors.white.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEditMode(List<SeatStudent> roster) {
    final validation = SeatingSaveValidator.validate(
      draftSeats: _draftSeats,
      roster: roster,
      lockedCount: _lockedCells.length,
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
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                      side: const BorderSide(color: Colors.red),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    onPressed: (_isSaving || _assignedCount == 0)
                        ? null
                        : _confirmClearAll,
                    icon: const Icon(Icons.delete_outline, size: 18),
                    label: const Text('Xóa toàn bộ'),
                  ),
                ),
                const SizedBox(height: 16),
                SeatingGrid(
                  rows: _rows,
                  cols: _cols,
                  seats: _draftSeats,
                  homeroomRoster: roster,
                  isEdit: true,
                  lockedCells: _lockedCells,
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

  Widget _buildViewMode(List<SeatStudent> roster, ClassInfo classInfo) {
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

  List<Widget> _buildAssignedView(List<SeatStudent> roster) {
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
        lockedCells: _lockedCells,
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

  List<Widget> _buildEmptyView(List<SeatStudent> roster) {
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
