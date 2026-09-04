import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../../core/models/student_model.dart';
import '../../../../../core/data/mock_homeroom.dart';
import '../widgets/seating_components.dart';

enum ManagerMode { view, edit }

class SeatingManagerScreen extends StatefulWidget {
  const SeatingManagerScreen({super.key});

  @override
  State<SeatingManagerScreen> createState() => _SeatingManagerScreenState();
}

class _SeatingManagerScreenState extends State<SeatingManagerScreen> {
  ManagerMode _mode = ManagerMode.view;

  // Cố định cấu hình sơ đồ từ Admin: 5 hàng x 8 cột = 40 chỗ
  final int _rows = 5;
  final int _cols = 8;

  late List<String?> _savedSeats;
  late List<String?> _draftSeats;

  @override
  void initState() {
    super.initState();
    // Khởi tạo danh sách 40 chỗ ngồi trống
    _savedSeats = List.filled(_rows * _cols, null);
    _draftSeats = List.filled(_rows * _cols, null);
  }

  // --- LOGIC FUNCTIONS ---
  int get _assignedCount =>
      (_mode == ManagerMode.edit ? _draftSeats : _savedSeats)
          .where((s) => s != null)
          .length;

  List<StudentModel> get _unassignedStudents {
    final usedIds = _draftSeats.where((s) => s != null).toSet();
    return homeroomRoster.where((s) => !usedIds.contains(s.id)).toList();
  }

  // Khi chạm vào ô trống
  void _tapCell(int index) {
    if (_mode == ManagerMode.edit && _draftSeats[index] == null) {
      _showStudentPicker(index);
    }
  }

  // Logic Hoán đổi khi Kéo - Thả
  void _onAcceptDrag(int draggedIndex, int targetIndex) {
    setState(() {
      final temp = _draftSeats[targetIndex];
      _draftSeats[targetIndex] = _draftSeats[draggedIndex];
      _draftSeats[draggedIndex] = temp;
    });
  }

  void _save() {
    setState(() {
      _savedSeats = List.from(_draftSeats);
      _mode = ManagerMode.view;
    });
  }

  // --- BUILD UI ---
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
                child: _mode == ManagerMode.edit
                    ? _buildEditMode()
                    : _buildViewMode(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    String title = _mode == ManagerMode.edit
        ? "Sắp xếp chỗ ngồi"
        : "Quản lý sơ đồ lớp";
    String subtitle = _mode == ManagerMode.edit
        ? "Sơ đồ ${_rows}x${_cols} · ${homeroomInfo['name']}"
        : "Lớp chủ nhiệm";

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
              onTap: () => setState(() => _mode = ManagerMode.view),
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

  Widget _buildEditMode() {
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
                  totalSize: homeroomInfo['size'] as int,
                ),
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

                // VẼ LƯỚI KÉO THẢ TẠI ĐÂY
                _buildDragAndDropGrid(isEdit: true),
              ],
            ),
          ),
        ),
        _buildBottomButton('Lưu sơ đồ', Icons.check, _save),
      ],
    );
  }

  Widget _buildViewMode() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
      child: Column(
        children: [
          HomeroomInfoCard(info: homeroomInfo),
          const SizedBox(height: 20),

          if (_assignedCount > 0) ...[
            CountCard(
              assignedCount: _assignedCount,
              totalSize: homeroomInfo['size'] as int,
            ),
            const SizedBox(height: 16),
            _buildDragAndDropGrid(
              isEdit: false,
            ), // Chế độ View không cho kéo thả
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
          ] else ...[
            // MÀN HÌNH TRỐNG: Đi thẳng vào chỉnh sửa
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
                    Text(
                      'Hệ thống đã chuẩn bị sẵn sơ đồ $_rows x$_cols. Nhấn để gán học sinh vào vị trí.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
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
                      icon: const Icon(
                        Icons.add,
                        size: 18,
                        color: Colors.white,
                      ),
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
          ],
        ],
      ),
    );
  }

  // --- GRID VIEW VỚI DRAG & DROP ---
  Widget _buildDragAndDropGrid({required bool isEdit}) {
    List<String?> dataSeats = isEdit ? _draftSeats : _savedSeats;

    return Column(
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 8),
          margin: const EdgeInsets.only(bottom: 20),
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
              letterSpacing: 2.0,
            ),
          ),
        ),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: _cols,
            crossAxisSpacing: 4,
            mainAxisSpacing: 4, // Thu hẹp khoảng cách vì nhiều cột
            childAspectRatio: 1.0,
          ),
          itemCount: _rows * _cols,
          itemBuilder: (context, index) {
            final studentId = dataSeats[index];

            // Widget lõi hiển thị 1 ô
            Widget cellContent = Container(
              decoration: BoxDecoration(
                color: studentId != null
                    ? const Color(0xFFE9F8EF)
                    : AppColors.appBg,
                border: Border.all(
                  color: studentId != null
                      ? const Color(0xFFBFE6CF)
                      : AppColors.hair,
                ),
                borderRadius: BorderRadius.circular(6), // Bo góc nhỏ hơn
              ),
              child: studentId != null
                  ? Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          homeroomRoster
                              .firstWhere((s) => s.id == studentId)
                              .short,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF137A41),
                          ), // Chữ nhỏ lại một chút
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    )
                  : (isEdit
                        ? const Icon(
                            Icons.add,
                            size: 14,
                            color: AppColors.muted,
                          )
                        : null),
            );

            if (!isEdit) return cellContent;

            // Nếu đang trong chế độ EDIT: Áp dụng Kéo Thả (DragTarget)
            return DragTarget<int>(
              onAccept: (draggedIndex) => _onAcceptDrag(draggedIndex, index),
              builder: (context, candidateData, rejectedData) {
                // Nếu ô được hover bởi người đang kéo, hiện khung màu xanh lam
                if (candidateData.isNotEmpty) {
                  return Container(
                    decoration: BoxDecoration(
                      color: AppColors.lightBlue,
                      border: Border.all(color: AppColors.brand, width: 2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                  );
                }

                // Nếu ô TRỐNG -> Chỉ có thể Tap để thêm
                if (studentId == null) {
                  return InkWell(
                    onTap: () => _tapCell(index),
                    child: cellContent,
                  );
                }

                // Nếu ô CÓ NGƯỜI -> Nhấn giữ để Kéo (Không có hàm onTap để tránh lỗi)
                return LongPressDraggable<int>(
                  data: index,
                  delay: const Duration(milliseconds: 150),
                  feedback: Material(
                    color: Colors.transparent,
                    child: Transform.scale(
                      scale: 1.2,
                      child: SizedBox(
                        width: MediaQuery.of(context).size.width / _cols - 4,
                        height: MediaQuery.of(context).size.width / _cols - 4,
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            border: Border.all(
                              color: AppColors.brand,
                              width: 2,
                            ),
                            borderRadius: BorderRadius.circular(6),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.2),
                                blurRadius: 10,
                                offset: const Offset(0, 5),
                              ),
                            ],
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            homeroomRoster
                                .firstWhere((s) => s.id == studentId)
                                .short,
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppColors.brand,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  childWhenDragging: Container(
                    decoration: BoxDecoration(
                      color: AppColors.appBg,
                      border: Border.all(color: AppColors.hair),
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                  child: cellContent, // Chỉ hiển thị cellContent, không bọc InkWell để vô hiệu hóa thao tác chạm
                );
              },
            );
          },
        ),
      ],
    );
  }

  // --- BUTTON Ở CUỐI MÀN HÌNH ---
  Widget _buildBottomButton(
    String label,
    IconData icon,
    VoidCallback onPressed,
  ) {
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
          onPressed: onPressed,
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

  // --- BOTTOM SHEET CHỌN HỌC SINH (GIỮ NGUYÊN) ---
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
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
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
                              'Đã xếp chỗ cho tất cả hoặc không tìm thấy.',
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
