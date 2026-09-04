import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';

// THÊM DÒNG NÀY ĐỂ KẾT NỐI VỚI MÀN HÌNH DANH SÁCH LỚP
import 'student_list_screen.dart';

// ==========================================
// 1. MOCK DATA & MODELS CHO SESSION DETAIL
// ==========================================
class SeatInfo {
  final String id;
  final String name;
  final String fullName;
  final String dob;
  final String parentPhone;
  bool present;
  bool distracted;
  int? attention;
  final List<int>? recentAttention; // Lịch sử tập trung 2 ngày gần nhất
  String note; // Ghi chú của giáo viên

  SeatInfo({
    required this.id,
    required this.name,
    required this.fullName,
    required this.dob,
    required this.parentPhone,
    required this.present,
    required this.distracted,
    this.attention,
    this.recentAttention,
    this.note = '',
  });
}

// Hàm giả lập tạo sơ đồ lớp (Đã thêm thông tin cá nhân và lịch sử)
List<SeatInfo> generateMockSeats(int rows, int cols, String status) {
  final List<String> initials = [
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
  ];

  bool isFuture = status == 'Sắp diễn ra';

  return List.generate(rows * cols, (index) {
    if (index >= initials.length) {
      return SeatInfo(
        id: '',
        name: '',
        fullName: '',
        dob: '',
        parentPhone: '',
        present: false,
        distracted: false,
      );
    }

    // Giả lập trạng thái điểm danh
    bool present = isFuture ? true : (index % 10) != 0;
    bool distracted = isFuture ? false : (present && (index % 7) == 0);
    int? attention = (!present || isFuture)
        ? null
        : (distracted ? 38 + ((index * 7) % 20) : 78 + ((index * 5) % 18));

    // Giả lập điểm 2 ngày trước (80% -> 100%)
    List<int>? recent = (!present && !isFuture)
        ? null
        : [85 + (index % 15), 80 + (index % 20)];

    return SeatInfo(
      id: 'HS${index.toString().padLeft(3, '0')}',
      name: initials[index],
      fullName: 'Nguyễn Văn ${initials[index]}',
      dob: '${(10 + (index % 20)).toString().padLeft(2, '0')}/05/2008',
      parentPhone: '0901 234 ${index.toString().padLeft(3, '0')}',
      present: present,
      distracted: distracted,
      attention: attention,
      recentAttention: recent,
      note: '', // Ban đầu ghi chú trống
    );
  });
}

// ==========================================
// 2. MÀN HÌNH CHÍNH (SESSION DETAIL SCREEN)
// ==========================================
class SessionDetailScreen extends StatefulWidget {
  final String classId;
  final String className;
  final String room;
  final String start;
  final String end;
  final String? date;
  final String status;

  const SessionDetailScreen({
    super.key,
    this.classId = '12A1',
    this.className = 'Lớp 12A1',
    this.room = 'A203',
    this.start = '08:00',
    this.end = '09:30',
    this.date = 'Hôm nay',
    this.status = 'Đang diễn ra',
  });

  @override
  State<SessionDetailScreen> createState() => _SessionDetailScreenState();
}

class _SessionDetailScreenState extends State<SessionDetailScreen> {
  final int rows = 6;
  final int cols = 7;
  late List<SeatInfo> seats;

  @override
  void initState() {
    super.initState();
    seats = generateMockSeats(rows, cols, widget.status);
  }

  @override
  Widget build(BuildContext context) {
    final total = rows * cols;
    final absent = seats.where((s) => !s.present && s.name.isNotEmpty).length;
    final present = seats.where((s) => s.present).length;
    final distracted = seats.where((s) => s.distracted).length;

    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          _buildHeader(),
          Expanded(
            child: Transform.translate(
              offset: const Offset(0, -16),
              child: Container(
                decoration: const BoxDecoration(
                  color: AppColors.appBg,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(24),
                    topRight: Radius.circular(24),
                  ),
                ),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
                  child: Column(
                    children: [
                      _buildInfoAndStatsCard(
                        total,
                        present,
                        absent,
                        distracted,
                      ),
                      const SizedBox(height: 20),

                      _buildSeatingChart(),

                      // =====================================
                      // ĐÃ THÊM LỐI TẮT DANH SÁCH LỚP Ở ĐÂY
                      // =====================================
                      const SizedBox(height: 20),
                      _buildClassListShortcut(),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
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
          InkWell(
            onTap: () => Navigator.pop(context),
            borderRadius: BorderRadius.circular(20),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.arrow_back,
                color: Colors.white,
                size: 22,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Chi tiết phiên',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${widget.className} · Phòng ${widget.room}',
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

  Widget _buildInfoAndStatsCard(
    int total,
    int present,
    int absent,
    int distracted,
  ) {
    bool isFuture = widget.status == 'Sắp diễn ra';

    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
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
                    widget.classId,
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
                      Row(
                        children: [
                          Text(
                            widget.className,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w800,
                              color: AppColors.navy,
                            ),
                          ),
                          if (widget.status == 'Đang diễn ra') ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE9F8EF),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                children: [
                                  _buildPulsingDot(),
                                  const SizedBox(width: 6),
                                  const Text(
                                    'Đang diễn ra',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF137A41),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
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
                                'Phòng ${widget.room}',
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
                                Icons.schedule,
                                size: 15,
                                color: AppColors.muted,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                '${widget.start} – ${widget.end}',
                                style: const TextStyle(
                                  fontSize: 13,
                                  color: AppColors.muted,
                                ),
                              ),
                            ],
                          ),
                          if (widget.date != null)
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.calendar_today_outlined,
                                  size: 15,
                                  color: AppColors.muted,
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  widget.date!,
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
            const SizedBox(height: 16),
            const Divider(height: 1, color: AppColors.hair),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildStatItem('Sĩ số', total.toString(), AppColors.navy),
                _buildDivider(),
                _buildStatItem(
                  'Có mặt',
                  isFuture ? '-' : present.toString(),
                  const Color(0xFF137A41),
                ),
                _buildDivider(),
                _buildStatItem(
                  'Vắng',
                  isFuture ? '-' : absent.toString(),
                  const Color(0xFF94A3B8),
                ),
                _buildDivider(),
                _buildStatItem(
                  'Mất tập trung',
                  isFuture ? '-' : distracted.toString(),
                  const Color(0xFFD9822B),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: value == '-' ? AppColors.muted : color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AppColors.muted),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildDivider() =>
      Container(height: 30, width: 1, color: AppColors.hair);

  Widget _buildSeatingChart() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text(
              'Sơ đồ lớp',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: AppColors.navy,
              ),
            ),
            Text(
              'Nhấn vào học sinh để xem',
              style: TextStyle(fontSize: 12, color: AppColors.muted),
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
          color: Colors.white,
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
                    final seat = seats[index];
                    if (seat.name.isEmpty) return const SizedBox.shrink();

                    Color bgColor, borderColor, textColor, dotColor;
                    if (widget.status == 'Sắp diễn ra') {
                      bgColor = AppColors.appBg;
                      borderColor = AppColors.hair;
                      textColor = AppColors.navy;
                      dotColor = AppColors.muted.withOpacity(0.3);
                    } else {
                      if (!seat.present) {
                        bgColor = AppColors.appBg;
                        borderColor = AppColors.hair;
                        textColor = const Color(0xFF94A3B8);
                        dotColor = const Color(0xFFCBD5E1);
                      } else if (seat.distracted) {
                        bgColor = const Color(0xFFFFF4E3);
                        borderColor = const Color(0xFFF0CFA0);
                        textColor = const Color(0xFF7A4D13);
                        dotColor = const Color(0xFFD9822B);
                      } else {
                        bgColor = const Color(0xFFE9F8EF);
                        borderColor = const Color(0xFFBFE6CF);
                        textColor = const Color(0xFF137A41);
                        dotColor = const Color(0xFF20A75A);
                      }
                    }

                    return InkWell(
                      onTap: () => _showStudentDetails(seat),
                      child: Container(
                        decoration: BoxDecoration(
                          color: bgColor,
                          border: Border.all(color: borderColor),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              seat.name,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: textColor,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Container(
                              width: 6,
                              height: 6,
                              decoration: BoxDecoration(
                                color: dotColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ],
                        ),
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

  Widget _buildPulsingDot() {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.5, end: 1.0),
      duration: const Duration(milliseconds: 1000),
      curve: Curves.easeInOut,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Container(
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              color: Color(0xFF20A75A),
              shape: BoxShape.circle,
            ),
          ),
        );
      },
      onEnd: () {},
    );
  }

  // --- HÀM BUILD LỐI TẮT DANH SÁCH LỚP ---
  Widget _buildClassListShortcut() {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () async {
          // Mở trang danh sách lớp và đợi khi quay lại để cập nhật sơ đồ (nếu điểm danh đổi)
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) =>
                  StudentListScreen(seats: seats, status: widget.status),
            ),
          );
          setState(() {});
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.appBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.hair),
                ),
                child: const Icon(
                  Icons.format_list_bulleted,
                  color: AppColors.navy,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Xem danh sách lớp',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppColors.navy,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Hiển thị dưới dạng danh sách cuộn',
                      style: TextStyle(fontSize: 12, color: AppColors.muted),
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

  // --- 3. BOTTOM SHEET CHI TIẾT HỌC SINH (NÂNG CẤP) ---
  void _showStudentDetails(SeatInfo student) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return StatefulBuilder(
          builder: (BuildContext context, StateSetter setSheetState) {
            final bottomInset = MediaQuery.of(context).viewInsets.bottom;

            return Container(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(context).size.height * 0.85,
              ),
              padding: EdgeInsets.fromLTRB(20, 12, 20, 28 + bottomInset),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppColors.hair,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // --- Avatar & Name ---
                    Row(
                      children: [
                        CircleAvatar(
                          radius: 26,
                          backgroundColor: AppColors.lightBlue,
                          child: Text(
                            student.name.substring(0, 1),
                            style: const TextStyle(
                              fontSize: 20,
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
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.navy,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  // COMBOBOX ĐIỂM DANH
                                  Container(
                                    height: 28,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 10,
                                    ),
                                    decoration: BoxDecoration(
                                      color: student.present
                                          ? const Color(0xFFE9F8EF)
                                          : AppColors.appBg,
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: DropdownButtonHideUnderline(
                                      child: DropdownButton<bool>(
                                        value: student.present,
                                        isDense: true,
                                        icon: Icon(
                                          Icons.keyboard_arrow_down,
                                          size: 16,
                                          color: student.present
                                              ? const Color(0xFF137A41)
                                              : AppColors.muted,
                                        ),
                                        items: [
                                          DropdownMenuItem(
                                            value: true,
                                            child: Row(
                                              children: [
                                                Container(
                                                  width: 6,
                                                  height: 6,
                                                  decoration:
                                                      const BoxDecoration(
                                                        color: Color(
                                                          0xFF20A75A,
                                                        ),
                                                        shape: BoxShape.circle,
                                                      ),
                                                ),
                                                const SizedBox(width: 6),
                                                const Text(
                                                  'Có mặt',
                                                  style: TextStyle(
                                                    fontSize: 11,
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
                                                  width: 6,
                                                  height: 6,
                                                  decoration:
                                                      const BoxDecoration(
                                                        color: Color(
                                                          0xFF94A3B8,
                                                        ),
                                                        shape: BoxShape.circle,
                                                      ),
                                                ),
                                                const SizedBox(width: 6),
                                                const Text(
                                                  'Vắng mặt',
                                                  style: TextStyle(
                                                    fontSize: 11,
                                                    fontWeight: FontWeight.bold,
                                                    color: AppColors.muted,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ],
                                        onChanged: (bool? newValue) {
                                          if (newValue != null &&
                                              newValue != student.present) {
                                            setSheetState(() {
                                              student.present = newValue;
                                              if (!newValue) {
                                                student.distracted = false;
                                                student.attention = null;
                                              } else {
                                                student.attention = 100;
                                              }
                                            });
                                            setState(() {});
                                          }
                                        },
                                      ),
                                    ),
                                  ),

                                  if (student.distracted) ...[
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 10,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFFFF4E3),
                                        borderRadius: BorderRadius.circular(20),
                                      ),
                                      child: Row(
                                        children: const [
                                          Icon(
                                            Icons.notifications_active_outlined,
                                            size: 12,
                                            color: Color(0xFFD9822B),
                                          ),
                                          SizedBox(width: 4),
                                          Text(
                                            'Mất tập trung',
                                            style: TextStyle(
                                              fontSize: 11,
                                              fontWeight: FontWeight.bold,
                                              color: Color(0xFFD9822B),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // --- Thông tin cá nhân ---
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.appBg,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.hair),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'THÔNG TIN CÁ NHÂN',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: AppColors.muted,
                              letterSpacing: 0.5,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              const Icon(
                                Icons.cake_outlined,
                                size: 16,
                                color: AppColors.brand,
                              ),
                              const SizedBox(width: 10),
                              Text(
                                'Ngày sinh: ${student.dob}',
                                style: const TextStyle(
                                  fontSize: 14,
                                  color: AppColors.navy,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              const Icon(
                                Icons.phone_android_outlined,
                                size: 16,
                                color: AppColors.brand,
                              ),
                              const SizedBox(width: 10),
                              Text(
                                'SĐT Phụ huynh: ${student.parentPhone}',
                                style: const TextStyle(
                                  fontSize: 14,
                                  color: AppColors.navy,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // --- Mức độ tập trung hiện tại & Lịch sử ---
                    if (student.attention != null &&
                        widget.status != 'Sắp diễn ra') ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Mức độ tập trung (Phiên này)',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: AppColors.navy,
                            ),
                          ),
                          Text(
                            '${student.attention}%',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w800,
                              color: student.distracted
                                  ? const Color(0xFFD9822B)
                                  : AppColors.brand,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: LinearProgressIndicator(
                          value: student.attention! / 100,
                          minHeight: 10,
                          backgroundColor: AppColors.appBg,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            student.distracted
                                ? const Color(0xFFD9822B)
                                : AppColors.brand,
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      if (student.recentAttention != null) ...[
                        const Text(
                          'Lịch sử tập trung (2 ngày gần nhất)',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppColors.navy,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: _buildRecentScoreCard(
                                'Hôm qua',
                                student.recentAttention![0],
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _buildRecentScoreCard(
                                'Hôm kia',
                                student.recentAttention![1],
                              ),
                            ),
                          ],
                        ),
                      ],

                      const SizedBox(height: 24),
                    ] else if (widget.status != 'Sắp diễn ra') ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(
                          vertical: 12,
                          horizontal: 16,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.appBg,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text(
                          'Học sinh vắng mặt — không có dữ liệu tập trung.',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.muted,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],

                    // --- Khu vực Ghi chú (Note) ---
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        'Ghi chú của giáo viên',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.navy,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      initialValue: student.note,
                      maxLines: 3,
                      onChanged: (val) {
                        student.note = val;
                      },
                      decoration: InputDecoration(
                        hintText: 'Nhập lý do vắng mặt, hoặc lý do mất tập trung (VD: Học sinh sốt cao xin nằm gục tại bàn)...',
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
                        contentPadding: const EdgeInsets.all(16),
                      ),
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.navy,
                      ),
                    ),

                    const SizedBox(height: 24),

                    // --- Nút Đóng ---
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.navy,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        onPressed: () => Navigator.pop(context),
                        child: const Text(
                          'Xác nhận & Đóng',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildRecentScoreCard(String label, int score) {
    Color color = score < 50 ? const Color(0xFFD9822B) : AppColors.brand;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.hair),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 12, color: AppColors.muted),
          ),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '$score',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: color,
                  height: 1.0,
                ),
              ),
              const SizedBox(width: 2),
              Text(
                '%',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
