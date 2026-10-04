import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../core/models/session_student_model.dart';
import '../controllers/session_detail_controller.dart';
import 'student_list_screen.dart';

// ==========================================
// 1. MODEL CHO SEAT INFO
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
  final List<int>? recentAttention;
  String note;

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

  SeatInfo copyWith({
    bool? present,
    bool? distracted,
    int? attention,
    String? note,
  }) {
    return SeatInfo(
      id: id,
      name: name,
      fullName: fullName,
      dob: dob,
      parentPhone: parentPhone,
      present: present ?? this.present,
      distracted: distracted ?? this.distracted,
      attention: attention ?? this.attention,
      recentAttention: recentAttention,
      note: note ?? this.note,
    );
  }
}

// ==========================================
// 2. MÀN HÌNH CHÍNH (SESSION DETAIL SCREEN)
// ==========================================
class SessionDetailScreen extends StatefulWidget {
  final String sessionId;
  final String classId;
  final String className;
  final String room;
  final String start;
  final String end;
  final String? date;
  final String status;

  const SessionDetailScreen({
    super.key,
    required this.sessionId,
    this.classId = '',
    this.className = 'Lớp học',
    this.room = 'N/A',
    this.start = '07:00',
    this.end = '09:00',
    this.date,
    this.status = 'Đang diễn ra',
  });

  @override
  State<SessionDetailScreen> createState() => _SessionDetailScreenState();
}

class _SessionDetailScreenState extends State<SessionDetailScreen> {
  late final SessionDetailController _controller;

  @override
  void initState() {
    super.initState();
    _controller = SessionDetailController(sessionId: widget.sessionId);
    _controller.addListener(_onControllerChanged);
  }

  void _onControllerChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _controller.removeListener(_onControllerChanged);
    _controller.dispose();
    super.dispose();
  }

  int get rows => _controller.classroomRows;
  int get cols => _controller.classroomColumns;

  List<SeatInfo> get seats {
    final sessionStudents = _controller.sessionStudents;
    final Map<String, SessionStudentModel> posMap = {};
    for (var s in sessionStudents) {
      posMap['${s.row},${s.column}'] = s;
    }

    return List.generate(rows * cols, (index) {
      final r0 = index ~/ cols;
      final c0 = index % cols;
      final r1 = r0 + 1;
      final c1 = c0 + 1;
      final sData = posMap['$r1,$c1'] ?? posMap['$r0,$c0'];

      if (sData == null) {
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

      final studentId = sData.studentId;
      final studentModel = _controller.getStudentInfo(studentId);
      final isPresent = sData.isPresent;
      final isAttention = sData.isAttention;
      final attentionScore =
          sData.attentionScore?.toInt() ?? (isPresent ? 85 : null);
      final note = sData.note;

      return SeatInfo(
        id: studentId,
        name:
            studentModel?.short ??
            (studentModel?.name.isNotEmpty == true
                ? studentModel!.name.split(' ').last
                : (studentId.isNotEmpty ? 'HS' : '')),
        fullName: studentModel?.name ?? 'Học sinh',
        dob: studentModel?.birthday ?? '',
        parentPhone: studentModel?.parentEmail.isNotEmpty == true
            ? studentModel!.parentEmail
            : (studentModel?.parentId ?? ''),
        present: isPresent,
        distracted: isPresent && !isAttention,
        attention: attentionScore,
        recentAttention: isPresent ? [85, 90] : null,
        note: note,
      );
    });
  }

  // Chuyển đổi trạng thái tuần tự: Có mặt -> Mất tập trung -> Vắng -> Có mặt
  void _toggleSeatStatus(SeatInfo seat) {
    if (seat.id.isEmpty) return;
    _controller.toggleAttendance(seat.id);
  }

  void _handleCancel() {
    _controller.cancelChanges();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Đã khôi phục lại dữ liệu gốc ban đầu!'),
        duration: Duration(seconds: 1),
      ),
    );
  }

  void _handleSave() async {
    final success = await _controller.saveChanges();
    if (!mounted) return;
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã lưu thay đổi thành công!'),
          backgroundColor: Color(0xFF137A41),
          duration: Duration(seconds: 2),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Lỗi khi lưu dữ liệu. Vui lòng thử lại!'),
          backgroundColor: Colors.redAccent,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final total = _controller.totalStudents;
    final present = _controller.presentCount;
    final absent = _controller.absentCount;
    final distracted = _controller.distractedCount;

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
                      const SizedBox(height: 16),
                      _buildActionButtons(),
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
                color: Colors.white.withValues(alpha: 0.1),
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
              'Chạm để đổi màu',
              style: TextStyle(fontSize: 11, color: AppColors.muted),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.hair),
          ),
          child: Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 8),
                margin: const EdgeInsets.only(bottom: 14),
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
                  crossAxisCount: cols,
                  crossAxisSpacing: 4,
                  mainAxisSpacing: 4,
                  childAspectRatio: 1.0,
                ),
                itemCount: rows * cols,
                itemBuilder: (context, index) {
                  final seat = seats[index];
                  final bool hasStudent = seat.name.isNotEmpty;

                  Color bgColor, borderColor, textColor;
                  if (!hasStudent) {
                    bgColor = AppColors.appBg;
                    borderColor = AppColors.hair;
                    textColor = Colors.transparent;
                  } else if (!seat.present) {
                    bgColor = const Color(0xFFF1F5F9);
                    borderColor = const Color(0xFFCBD5E1);
                    textColor = const Color(0xFF64748B);
                  } else if (seat.distracted) {
                    bgColor = const Color(0xFFFFF4E3);
                    borderColor = const Color(0xFFF0CFA0);
                    textColor = const Color(0xFF7A4D13);
                  } else {
                    bgColor = const Color(0xFFE9F8EF);
                    borderColor = const Color(0xFFBFE6CF);
                    textColor = const Color(0xFF137A41);
                  }

                  return InkWell(
                    onTap: hasStudent ? () => _toggleSeatStatus(seat) : null,
                    onLongPress: hasStudent
                        ? () => _showStudentDetails(seat)
                        : null,
                    borderRadius: BorderRadius.circular(6),
                    child: Container(
                      decoration: BoxDecoration(
                        color: bgColor,
                        border: Border.all(color: borderColor),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        seat.name,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: textColor,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }

  // --- 2 NÚT LƯU VÀ HỦY ---
  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: SizedBox(
            height: 44,
            child: OutlinedButton(
              style: OutlinedButton.styleFrom(
                side: BorderSide(
                  color: _controller.hasChanges && !_controller.isSaving
                      ? Colors.redAccent
                      : AppColors.hair,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                backgroundColor: Colors.white,
              ),
              onPressed: _controller.hasChanges && !_controller.isSaving
                  ? _handleCancel
                  : null,
              child: Text(
                'Hủy thay đổi',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: _controller.hasChanges && !_controller.isSaving
                      ? Colors.redAccent
                      : AppColors.muted,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: SizedBox(
            height: 44,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: _controller.hasChanges && !_controller.isSaving
                    ? AppColors.navy
                    : Colors.grey.shade300,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onPressed: _controller.hasChanges && !_controller.isSaving
                  ? _handleSave
                  : null,
              child: _controller.isSaving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text(
                      'Lưu thay đổi',
                      style: TextStyle(
                        fontSize: 14,
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
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) =>
                  StudentListScreen(seats: seats, status: widget.status),
            ),
          );
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
                                            _controller
                                                .updateStudentSessionData(
                                                  student.id,
                                                  isPresent: newValue,
                                                  isAttention: newValue
                                                      ? true
                                                      : false,
                                                );
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
                        _controller.updateStudentSessionData(
                          student.id,
                          isPresent: student.present,
                          isAttention: !student.distracted,
                          note: val,
                        );
                      },
                      decoration: InputDecoration(
                        hintText:
                            'Nhập lý do vắng mặt, hoặc lý do mất tập trung...',
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
