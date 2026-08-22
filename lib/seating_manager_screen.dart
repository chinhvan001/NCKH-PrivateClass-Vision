import 'package:flutter/material.dart';

import 'account_screen.dart'; // Import để dùng chung AppColors

// --- MOCK DATA ---
class StudentModel {
  final String id;
  final String name;
  final String short;
  const StudentModel({
    required this.id,
    required this.name,
    required this.short,
  });
}

const homeroomInfo = {
  'id': '12A1',
  'name': 'Lớp chủ nhiệm 12A1',
  'room': 'A203',
  'schedule': 'Sáng thứ 2 - 6',
  'size': 42,
};

// Dữ liệu 42 học sinh mẫu
final List<StudentModel> homeroomRoster =
    [
          'An',
          'Bảo',
          'Cường',
          'Dũng',
          'Hà',
          'Huy',
          'Khang',
          'Linh',
          'Minh',
          'Nam',
          'Ngọc',
          'Oanh',
          'Phúc',
          'Quân',
          'Sơn',
          'Trang',
          'Tú',
          'Uyên',
          'Vy',
          'Yến',
          'Bình',
          'Châu',
          'Đạt',
          'Hương',
          'Kiên',
          'Lan',
          'Mai',
          'Nhung',
          'Phong',
          'Quỳnh',
          'Sang',
          'Thảo',
          'Trí',
          'Vân',
          'Việt',
          'Xuân',
          'Ánh',
          'Diệp',
          'Hòa',
          'Long',
          'Tâm',
          'Yên',
        ]
        .asMap()
        .entries
        .map(
          (e) => StudentModel(
            id: 'HS${e.key.toString().padLeft(3, '0')}',
            name: 'Nguyễn Văn ${e.value}',
            short: e.value,
          ),
        )
        .toList();

enum ManagerMode { view, size, edit }

// ==========================================
// MÀN HÌNH SEATING MANAGER
// ==========================================
class SeatingManagerScreen extends StatefulWidget {
  const SeatingManagerScreen({super.key});

  @override
  State<SeatingManagerScreen> createState() => _SeatingManagerScreenState();
}

class _SeatingManagerScreenState extends State<SeatingManagerScreen> {
  ManagerMode _mode = ManagerMode.view;

  // Dữ liệu đã lưu
  int _savedRows = 0;
  int _savedCols = 0;
  List<String?> _savedSeats = [];

  // Dữ liệu nháp (Đang chỉnh sửa)
  int _draftRows = 5;
  int _draftCols = 6;
  List<String?> _draftSeats = [];

  int? _selectedCell;

  // --- LOGIC XỬ LÝ ---

  int get _assignedCount {
    final target = _mode == ManagerMode.edit ? _draftSeats : _savedSeats;
    return target.where((s) => s != null).length;
  }

  List<StudentModel> get _unassignedStudents {
    final usedIds = _draftSeats.where((s) => s != null).toSet();
    return homeroomRoster.where((s) => !usedIds.contains(s.id)).toList();
  }

  void _confirmSize() {
    setState(() {
      if (_savedSeats.isNotEmpty) {
        // Cắt/Giữ lại học sinh theo ma trận mới
        List<String?> next = List.filled(_draftRows * _draftCols, null);
        for (int r = 0; r < _draftRows && r < _savedRows; r++) {
          for (int c = 0; c < _draftCols && c < _savedCols; c++) {
            next[r * _draftCols + c] = _draftSeats[r * _savedCols + c];
          }
        }
        _draftSeats = next;
      } else {
        // Khởi tạo mới hoàn toàn
        _draftSeats = List.filled(_draftRows * _draftCols, null);
      }
      _selectedCell = null;
      _mode = ManagerMode.edit;
    });
  }

  void _tapCell(int index) {
    setState(() {
      if (_selectedCell == null) {
        if (_draftSeats[index] != null) {
          _selectedCell = index; // Chọn để đổi chỗ
        } else {
          _showStudentPicker(index); // Chọn học sinh điền vào ô trống
        }
        return;
      }

      if (_selectedCell == index) {
        _selectedCell = null; // Bỏ chọn
        return;
      }

      // Đổi chỗ
      final tmp = _draftSeats[index];
      _draftSeats[index] = _draftSeats[_selectedCell!];
      _draftSeats[_selectedCell!] = tmp;
      _selectedCell = null;
    });
  }

  void _removeFromCell(int index) {
    setState(() {
      _draftSeats[index] = null;
      _selectedCell = null;
    });
  }

  void _save() {
    setState(() {
      _savedRows = _draftRows;
      _savedCols = _draftCols;
      _savedSeats = List.from(_draftSeats);
      _selectedCell = null;
      _mode = ManagerMode.view;
    });
  }

  // --- HÀM BUILD CHÍNH ---
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          _buildHeader(),
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
                child: _buildBodyContent(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBodyContent() {
    switch (_mode) {
      case ManagerMode.size:
        return _buildSizeMode();
      case ManagerMode.edit:
        return _buildEditMode();
      case ManagerMode.view:
        return _buildViewMode();
    }
  }

  // ==================== CÁC PHẦN UI CON ====================

  Widget _buildHeader() {
    String title = "Quản lý sơ đồ lớp";
    String subtitle = "Lớp chủ nhiệm";
    Widget? rightWidget;

    if (_mode == ManagerMode.size) {
      title = "Chọn kích thước";
      subtitle = "Bước 1 · Kích thước ma trận";
    } else if (_mode == ManagerMode.edit) {
      title = "Sắp xếp chỗ ngồi";
      subtitle = "$_draftRows × $_draftCols · ${homeroomInfo['name']}";
      rightWidget = InkWell(
        onTap: () => setState(() => _mode = ManagerMode.size),
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.brand.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Text(
            'Đổi kích thước',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: AppColors.brand,
            ),
          ),
        ),
      );
    }

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
          if (_mode != ManagerMode.view) ...[
            InkWell(
              onTap: () => setState(() => _mode = ManagerMode.view),
              borderRadius: BorderRadius.circular(20),
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
            const SizedBox(width: 12),
          ] else ...[
            // Nếu màn hình này gắn ở Bottom Navigation Bar, có thể bỏ nút Back ở View Mode
            const SizedBox(width: 4),
          ],

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
                const SizedBox(height: 2),
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
          if (rightWidget != null) rightWidget,
        ],
      ),
    );
  }

  // --- BƯỚC 1: CHỌN KÍCH THƯỚC ---
  Widget _buildSizeMode() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Chọn số hàng và số cột cho sơ đồ chỗ ngồi của lớp.',
                  style: TextStyle(fontSize: 13, color: AppColors.muted),
                ),
                const SizedBox(height: 16),
                _buildStepper(
                  'Số hàng (n)',
                  _draftRows,
                  (val) => setState(() => _draftRows = val),
                ),
                const SizedBox(height: 12),
                _buildStepper(
                  'Số cột (m)',
                  _draftCols,
                  (val) => setState(() => _draftCols = val),
                ),
                const SizedBox(height: 16),
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: const BorderSide(color: AppColors.hair),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 20),
                    child: Center(
                      child: Column(
                        children: [
                          const Text(
                            'Tổng số vị trí',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.muted,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '$_draftRows × $_draftCols = ${_draftRows * _draftCols}',
                            style: const TextStyle(
                              fontSize: 30,
                              fontWeight: FontWeight.w900,
                              color: AppColors.navy,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: AppColors.hair)),
          ),
          child: SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.brand,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 0,
              ),
              onPressed: _confirmSize,
              child: const Text(
                'Xác nhận kích thước',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStepper(String label, int value, Function(int) onChanged) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: AppColors.navy,
                  ),
                ),
                const Text(
                  'Từ 1 đến 10',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
              ],
            ),
            Row(
              children: [
                InkWell(
                  onTap: () => onChanged(value > 1 ? value - 1 : 1),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      border: Border.all(color: AppColors.hair),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.remove,
                      size: 20,
                      color: AppColors.navy,
                    ),
                  ),
                ),
                SizedBox(
                  width: 40,
                  child: Text(
                    value.toString(),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: AppColors.navy,
                    ),
                  ),
                ),
                InkWell(
                  onTap: () => onChanged(value < 10 ? value + 1 : 10),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      border: Border.all(color: AppColors.hair),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.add,
                      size: 20,
                      color: AppColors.navy,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // --- BƯỚC 2: CHỈNH SỬA SƠ ĐỒ ---
  Widget _buildEditMode() {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildCountCard(),
                const SizedBox(height: 12),
                Text(
                  _selectedCell == null
                      ? 'Nhấn vào ô trống để gán học sinh. Nhấn vào một học sinh để di chuyển hoặc đổi chỗ.'
                      : 'Nhấn vào ô trống để di chuyển, hoặc nhấn học sinh khác để đổi chỗ.',
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.muted,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 16),
                _buildMatrixCard(isEdit: true),

                if (_selectedCell != null &&
                    _draftSeats[_selectedCell!] != null) ...[
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.redAccent),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: () => _removeFromCell(_selectedCell!),
                      child: const Text(
                        'Bỏ học sinh khỏi ô này',
                        style: TextStyle(
                          color: Colors.redAccent,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        Container(
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
              onPressed: _save,
              icon: const Icon(Icons.check, size: 20, color: Colors.white),
              label: const Text(
                'Lưu sơ đồ',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // --- BƯỚC 3: XEM SƠ ĐỒ ---
  Widget _buildViewMode() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      child: Column(
        children: [
          _buildInfoCard(),
          const SizedBox(height: 20),

          if (_savedSeats.isNotEmpty) ...[
            _buildCountCard(),
            const SizedBox(height: 16),
            _buildMatrixCard(isEdit: false),
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
                onPressed: () {
                  setState(() {
                    _draftSeats = List.from(_savedSeats);
                    _draftRows = _savedRows;
                    _draftCols = _savedCols;
                    _selectedCell = null;
                    _mode = ManagerMode.edit;
                  });
                },
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
          ] else ...[
            Card(
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.hair),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 40,
                ),
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
                    const Text(
                      'Thiết lập sơ đồ chỗ ngồi cho lớp chủ nhiệm bằng cách chọn kích thước ma trận rồi gán học sinh vào từng vị trí.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 13, color: AppColors.muted),
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
                      onPressed: () {
                        setState(() {
                          _draftRows = 5;
                          _draftCols = 6;
                          _mode = ManagerMode.size;
                        });
                      },
                      icon: const Icon(
                        Icons.add,
                        size: 18,
                        color: Colors.white,
                      ),
                      label: const Text(
                        'Thiết lập sơ đồ lớp',
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
          ],
        ],
      ),
    );
  }

  // --- CÁC WIDGET DÙNG CHUNG (INFO & MATRIX) ---
  Widget _buildInfoCard() {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.brand, Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                homeroomInfo['id'].toString(),
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    homeroomInfo['name'].toString(),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppColors.navy,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 16,
                    runSpacing: 4,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.home_outlined,
                            size: 15,
                            color: AppColors.brand,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'Phòng ${homeroomInfo['room']}',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: AppColors.brand,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.people_alt_outlined,
                            size: 15,
                            color: AppColors.muted,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '${homeroomInfo['size']} học sinh',
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCountCard() {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Sĩ số lớp',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
                Text(
                  '${homeroomInfo['size']} học sinh',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AppColors.navy,
                  ),
                ),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const Text(
                  'Đã xếp chỗ',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
                Text(
                  '$_assignedCount/${homeroomInfo['size']}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AppColors.brand,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMatrixCard({required bool isEdit}) {
    final rows = isEdit ? _draftRows : _savedRows;
    final cols = isEdit ? _draftCols : _savedCols;
    final seats = isEdit ? _draftSeats : _savedSeats;

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Sơ đồ lớp',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: AppColors.navy,
              ),
            ),
            Text(
              '$rows × $cols vị trí',
              style: const TextStyle(fontSize: 12, color: AppColors.muted),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Card(
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: AppColors.hair),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Container(
                  width: 150,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.navy,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  alignment: Alignment.center,
                  child: const Text(
                    'BỤC GIẢNG',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      letterSpacing: 1.0,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: cols,
                    crossAxisSpacing: 6,
                    mainAxisSpacing: 6,
                    childAspectRatio: 1.0,
                  ),
                  itemCount: rows * cols,
                  itemBuilder: (context, index) {
                    final studentId = seats[index];
                    final student = studentId != null
                        ? homeroomRoster.firstWhere((s) => s.id == studentId)
                        : null;
                    final isSel = _selectedCell == index;

                    Color bgColor = AppColors.appBg;
                    Color borderColor = AppColors.hair;
                    Color textColor = Colors.transparent;
                    Widget content = const SizedBox();

                    if (student != null) {
                      bgColor = isSel
                          ? AppColors.lightBlue
                          : AppColors.lightBlue.withOpacity(0.5);
                      borderColor = isSel ? AppColors.brand : AppColors.hair;
                      textColor = AppColors.navy;
                      content = Text(
                        student.short,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: textColor,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      );
                    } else if (isEdit) {
                      bgColor = _selectedCell != null
                          ? AppColors.lightBlue.withOpacity(0.2)
                          : Colors.white;
                      borderColor = AppColors.brand.withOpacity(0.4);
                      content = const Icon(
                        Icons.add,
                        size: 14,
                        color: AppColors.brand,
                      );
                    }

                    return InkWell(
                      onTap: isEdit ? () => _tapCell(index) : null,
                      child: Container(
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: bgColor,
                          border: Border.all(
                            color: borderColor,
                            style: (student == null && isEdit)
                                ? BorderStyle.solid
                                : BorderStyle.solid,
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: content,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // --- BỘ CHỌN HỌC SINH (BOTTOM SHEET) ---
  void _showStudentPicker(int cellIndex) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        String query = '';

        return StatefulBuilder(
          builder: (context, setSheetState) {
            final list = _unassignedStudents
                .where(
                  (s) =>
                      s.name.toLowerCase().contains(query.trim().toLowerCase()),
                )
                .toList();

            return Container(
              height: MediaQuery.of(context).size.height * 0.75,
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                ),
              ),
              child: Column(
                children: [
                  Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: AppColors.hair,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Chọn học sinh',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: AppColors.navy,
                        ),
                      ),
                      Text(
                        'Còn ${_unassignedStudents.length} chưa xếp',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.muted,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Container(
                    height: 44,
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: AppColors.appBg,
                      border: Border.all(color: AppColors.hair),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.search,
                          color: AppColors.muted,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextField(
                            onChanged: (val) =>
                                setSheetState(() => query = val),
                            decoration: const InputDecoration(
                              hintText: 'Tìm học sinh...',
                              hintStyle: TextStyle(color: Colors.black38),
                              border: InputBorder.none,
                              isDense: true,
                            ),
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.navy,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: list.isEmpty
                        ? const Center(
                            child: Text(
                              'Đã xếp chỗ cho tất cả học sinh hoặc không tìm thấy.',
                              style: TextStyle(
                                fontSize: 14,
                                color: AppColors.muted,
                              ),
                            ),
                          )
                        : ListView.builder(
                            itemCount: list.length,
                            itemBuilder: (context, index) {
                              final s = list[index];
                              return Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: InkWell(
                                  onTap: () {
                                    setState(() {
                                      _draftSeats[cellIndex] = s.id;
                                    });
                                    Navigator.pop(context);
                                  },
                                  child: Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      border: Border.all(color: AppColors.hair),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Row(
                                      children: [
                                        CircleAvatar(
                                          radius: 16,
                                          backgroundColor: AppColors.brand,
                                          child: Text(
                                            s.short[0],
                                            style: const TextStyle(
                                              color: Colors.white,
                                              fontSize: 12,
                                            ),
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Text(
                                            s.name,
                                            style: const TextStyle(
                                              fontSize: 14,
                                              fontWeight: FontWeight.bold,
                                              color: AppColors.navy,
                                            ),
                                          ),
                                        ),
                                        const Icon(
                                          Icons.add,
                                          color: AppColors.brand,
                                          size: 20,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
