import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
// Import file session_detail_screen để lấy model SeatInfo
import 'session_detail_screen.dart';

// ==========================================
// 1. MÀN HÌNH DANH SÁCH HỌC SINH (LIST VIEW)
// ==========================================
class StudentListScreen extends StatefulWidget {
  final List<SeatInfo> seats;
  final String status;

  const StudentListScreen({
    super.key,
    required this.seats,
    required this.status,
  });

  @override
  State<StudentListScreen> createState() => _StudentListScreenState();
}

class _StudentListScreenState extends State<StudentListScreen> {
  @override
  Widget build(BuildContext context) {
    // Lọc bỏ các ghế trống và sắp xếp theo tên ABC
    final validStudents = widget.seats.where((s) => s.name.isNotEmpty).toList();
    validStudents.sort((a, b) => a.name.compareTo(b.name));

    return Scaffold(
      backgroundColor: AppColors.appBg,
      appBar: AppBar(
        backgroundColor: AppColors.navy,
        elevation: 0,
        centerTitle: true,
        title: Column(
          children: [
            const Text(
              'Danh sách học sinh',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            Text(
              '${validStudents.length} học sinh',
              style: TextStyle(
                fontSize: 12,
                color: Colors.white.withOpacity(0.7),
              ),
            ),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: validStudents.length,
        separatorBuilder: (context, index) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final student = validStudents[index];
          return _buildStudentListItem(student);
        },
      ),
    );
  }

  Widget _buildStudentListItem(SeatInfo student) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () async {
          // Mở màn hình Chi tiết Cá nhân và chờ khi quay lại để cập nhật State
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => StudentDetailScreen(
                student: student,
                sessionStatus: widget.status,
              ),
            ),
          );
          setState(() {}); // Cập nhật lại danh sách nếu có thay đổi điểm danh
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: AppColors.lightBlue,
                child: Text(
                  student.name.substring(0, 1),
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    color: AppColors.brand,
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      student.fullName,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppColors.navy,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: student.present
                                ? const Color(0xFF20A75A)
                                : const Color(0xFF94A3B8),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          student.present ? 'Có mặt' : 'Vắng mặt',
                          style: TextStyle(
                            fontSize: 12,
                            color: student.present
                                ? const Color(0xFF137A41)
                                : AppColors.muted,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.black26),
            ],
          ),
        ),
      ),
    );
  }
}

// ==========================================
// 2. MÀN HÌNH CHI TIẾT CÁ NHÂN (FULL SCREEN)
// ==========================================
class StudentDetailScreen extends StatefulWidget {
  final SeatInfo student;
  final String sessionStatus;

  const StudentDetailScreen({
    super.key,
    required this.student,
    required this.sessionStatus,
  });

  @override
  State<StudentDetailScreen> createState() => _StudentDetailScreenState();
}

class _StudentDetailScreenState extends State<StudentDetailScreen> {
  late TextEditingController _noteController;

  @override
  void initState() {
    super.initState();
    _noteController = TextEditingController(text: widget.student.note);
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.student;

    return Scaffold(
      backgroundColor: AppColors.appBg,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.navy),
        title: const Text(
          'Hồ sơ học sinh',
          style: TextStyle(
            color: AppColors.navy,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: AppColors.hair, height: 1),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Khối 1: Avatar & Dropdown Điểm danh
            Card(
              elevation: 0,
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.hair),
              ),
              color: Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 40,
                      backgroundColor: AppColors.lightBlue,
                      child: Text(
                        s.name.substring(0, 1),
                        style: const TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.bold,
                          color: AppColors.brand,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      s.fullName,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                        color: AppColors.navy,
                      ),
                    ),
                    Text(
                      'Mã HS: ${s.id}',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Combobox Điểm danh
                    Container(
                      height: 36,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: s.present
                            ? const Color(0xFFE9F8EF)
                            : AppColors.appBg,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.hair),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<bool>(
                          value: s.present,
                          icon: Icon(
                            Icons.keyboard_arrow_down,
                            color: s.present
                                ? const Color(0xFF137A41)
                                : AppColors.muted,
                          ),
                          items: [
                            DropdownMenuItem(
                              value: true,
                              child: Row(
                                children: [
                                  Container(
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(
                                      color: Color(0xFF20A75A),
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text(
                                    'Đã có mặt',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF137A41),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            DropdownMenuItem(
                              value: false,
                              child: Row(
                                children: [
                                  Container(
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(
                                      color: Color(0xFF94A3B8),
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text(
                                    'Vắng mặt',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.muted,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() {
                                s.present = val;
                                if (!val) {
                                  s.distracted = false;
                                  s.attention = null;
                                } else {
                                  s.attention = 100;
                                }
                              });
                            }
                          },
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Khối 2: Thông tin cá nhân
            _buildSectionCard(
              title: 'THÔNG TIN CÁ NHÂN',
              child: Column(
                children: [
                  _buildInfoRow(Icons.cake_outlined, 'Ngày sinh', s.dob),
                  const Divider(height: 24, color: AppColors.hair),
                  _buildInfoRow(
                    Icons.phone_android_outlined,
                    'Phụ huynh',
                    s.parentPhone,
                    isHighlight: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Khối 3: Thống kê tập trung
            if (widget.sessionStatus != 'Sắp diễn ra' && s.attention != null)
              _buildSectionCard(
                title: 'MỨC ĐỘ TẬP TRUNG',
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Phiên hiện tại',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.navy,
                          ),
                        ),
                        Text(
                          '${s.attention}%',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            color: s.distracted
                                ? const Color(0xFFD9822B)
                                : AppColors.brand,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: LinearProgressIndicator(
                        value: s.attention! / 100,
                        minHeight: 10,
                        backgroundColor: AppColors.appBg,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          s.distracted
                              ? const Color(0xFFD9822B)
                              : AppColors.brand,
                        ),
                      ),
                    ),
                    if (s.recentAttention != null) ...[
                      const SizedBox(height: 24),
                      const Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          'Lịch sử 2 ngày trước',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.muted,
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _buildRecentBox(
                              'Hôm qua',
                              s.recentAttention![0],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildRecentBox(
                              'Hôm kia',
                              s.recentAttention![1],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            const SizedBox(height: 16),

            // Khối 4: Ghi chú
            _buildSectionCard(
              title: 'GHI CHÚ CỦA GIÁO VIÊN',
              child: TextFormField(
                controller: _noteController,
                maxLines: 4,
                onChanged: (val) => s.note = val,
                decoration: InputDecoration(
                  hintText: 'Nhập lý do vắng mặt hoặc lý do sức khỏe...',
                  hintStyle: const TextStyle(
                    fontSize: 13,
                    color: Colors.black38,
                  ),
                  filled: true,
                  fillColor: AppColors.appBg,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard({required String title, required Widget child}) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: AppColors.muted,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 16),
            child,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(
    IconData icon,
    String label,
    String value, {
    bool isHighlight = false,
  }) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppColors.muted),
        const SizedBox(width: 12),
        Text(
          label,
          style: const TextStyle(fontSize: 14, color: AppColors.muted),
        ),
        const Spacer(),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: isHighlight ? FontWeight.bold : FontWeight.w600,
            color: isHighlight ? AppColors.brand : AppColors.navy,
          ),
        ),
      ],
    );
  }

  Widget _buildRecentBox(String label, int score) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.hair),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 4),
          Text(
            '$score%',
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.navy,
            ),
          ),
        ],
      ),
    );
  }
}
