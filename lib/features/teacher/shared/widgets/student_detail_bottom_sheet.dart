import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/student_model.dart';
import '../../../../core/services/student_profile_service.dart';
import '../../session_detail/screens/session_detail_screen.dart';

class StudentDetailBottomSheet extends StatefulWidget {
  final String studentId;
  final String classId;
  final StudentModel? studentModel;
  final SeatInfo? seatInfo;
  final String? sessionStatus;
  final Function(bool isPresent, bool isAttention, String note)? onSessionUpdated;

  const StudentDetailBottomSheet({
    super.key,
    required this.studentId,
    required this.classId,
    this.studentModel,
    this.seatInfo,
    this.sessionStatus,
    this.onSessionUpdated,
  });

  static Future<void> show({
    required BuildContext context,
    required String studentId,
    required String classId,
    StudentModel? studentModel,
    SeatInfo? seatInfo,
    String? sessionStatus,
    Function(bool isPresent, bool isAttention, String note)? onSessionUpdated,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StudentDetailBottomSheet(
        studentId: studentId,
        classId: classId,
        studentModel: studentModel,
        seatInfo: seatInfo,
        sessionStatus: sessionStatus,
        onSessionUpdated: onSessionUpdated,
      ),
    );
  }

  @override
  State<StudentDetailBottomSheet> createState() =>
      _StudentDetailBottomSheetState();
}

class _StudentDetailBottomSheetState extends State<StudentDetailBottomSheet> {
  final StudentProfileService _service = StudentProfileService();
  bool _isLoading = true;
  StudentFullProfile? _profile;

  late bool _currentPresent;
  late bool _currentDistracted;
  late TextEditingController _noteController;

  @override
  void initState() {
    super.initState();
    _currentPresent = widget.seatInfo?.present ?? true;
    _currentDistracted = widget.seatInfo?.distracted ?? false;
    _noteController =
        TextEditingController(text: widget.seatInfo?.note ?? '');
    _loadData();
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final profile = await _service.getStudentFullProfile(
      studentId: widget.studentId,
      classId: widget.classId,
      initialStudentModel: widget.studentModel,
    );
    if (mounted) {
      setState(() {
        _profile = profile;
        _isLoading = false;
      });
    }
  }

  void _copyToClipboard(String text, String label) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Đã sao chép $label: $text'),
        backgroundColor: AppColors.navy,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final maxH = MediaQuery.of(context).size.height * 0.88;

    return Container(
      constraints: BoxConstraints(maxHeight: maxH),
      padding: EdgeInsets.fromLTRB(20, 12, 20, 24 + bottomInset),
      decoration: const BoxDecoration(
        color: AppColors.appBg,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(AppColors.navy),
                    ),
                  )
                : SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildStudentHeader(),
                        const SizedBox(height: 16),
                        if (_profile!.stats.isFrequentlyAbsent) ...[
                          _buildFrequentAbsenceWarning(),
                          const SizedBox(height: 16),
                        ],
                        _buildParentSection(),
                        const SizedBox(height: 16),
                        _buildAttendanceStatsSection(),
                        const SizedBox(height: 16),
                        _buildAttentionSection(),
                        const SizedBox(height: 16),
                        if (widget.seatInfo != null) ...[
                          _buildCurrentSessionSection(),
                          const SizedBox(height: 16),
                        ],
                      ],
                    ),
                  ),
          ),
          const SizedBox(height: 12),
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
              onPressed: () {
                if (widget.seatInfo != null) {
                  widget.seatInfo!.present = _currentPresent;
                  widget.seatInfo!.distracted = _currentDistracted;
                  widget.seatInfo!.note = _noteController.text;
                  widget.onSessionUpdated?.call(
                    _currentPresent,
                    !_currentDistracted,
                    _noteController.text,
                  );
                }
                Navigator.pop(context);
              },
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
    );
  }

  Widget _buildStudentHeader() {
    final s = _profile!.student;
    final initial = s.name.isNotEmpty ? s.name.substring(0, 1).toUpperCase() : 'H';

    return Row(
      children: [
        CircleAvatar(
          radius: 28,
          backgroundColor: AppColors.lightBlue,
          child: Text(
            initial,
            style: const TextStyle(
              fontSize: 22,
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
                s.name,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.navy,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.hair),
                    ),
                    child: Text(
                      'Mã: ${s.id.length > 8 ? s.id.substring(0, 8) : s.id}',
                      style: const TextStyle(fontSize: 11, color: AppColors.muted),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: s.isStudying ? const Color(0xFFDCFCE7) : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      s.isStudying ? 'Đang học' : 'Đã nghỉ',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: s.isStudying ? const Color(0xFF16A34A) : AppColors.muted,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildFrequentAbsenceWarning() {
    final stats = _profile!.stats;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFCA5A5)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.warning_amber_rounded, color: Color(0xFFDC2626), size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'CẢNH BÁO VẮNG HỌC THƯỜNG XUYÊN',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF991B1B)),
                ),
                const SizedBox(height: 4),
                Text(
                  stats.warningMessage,
                  style: const TextStyle(fontSize: 12, color: Color(0xFF7F1D1D), height: 1.3),
                ),
                if (_profile!.parentPhone.isNotEmpty && _profile!.parentPhone != 'Chưa cập nhật') ...[
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: () => _copyToClipboard(_profile!.parentPhone, 'SĐT Phụ huynh'),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.phone, size: 13, color: Color(0xFFDC2626)),
                        const SizedBox(width: 4),
                        Text(
                          'Gọi/Sao chép SĐT PH (${_profile!.parentPhone})',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFFDC2626)),
                        ),
                        const SizedBox(width: 4),
                        const Icon(Icons.copy, size: 12, color: Color(0xFFDC2626)),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildParentSection() {
    final p = _profile!;
    return _buildCardWrapper(
      title: 'THÔNG TIN PHỤ HUYNH',
      trailingWidget: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          color: p.isParentLinked ? const Color(0xFFDCFCE7) : const Color(0xFFFEF3C7),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          p.isParentLinked ? 'Đã liên kết' : 'Chưa liên kết',
          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: p.isParentLinked ? const Color(0xFF16A34A) : const Color(0xFFD97706)),
        ),
      ),
      child: Column(
        children: [
          _buildInfoRow(Icons.person_outline, 'Họ tên PH', p.parentDisplayName),
          const Divider(height: 20, color: AppColors.hair),
          Row(
            children: [
              const Icon(Icons.phone_outlined, size: 18, color: AppColors.muted),
              const SizedBox(width: 10),
              const Text('SĐT Phụ huynh', style: TextStyle(fontSize: 13, color: AppColors.muted)),
              const Spacer(),
              InkWell(
                onTap: p.parentPhone != 'Chưa cập nhật' ? () => _copyToClipboard(p.parentPhone, 'SĐT Phụ huynh') : null,
                child: Row(
                  children: [
                    Text(
                      p.parentPhone,
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: p.parentPhone != 'Chưa cập nhật' ? AppColors.brand : AppColors.navy),
                    ),
                    if (p.parentPhone != 'Chưa cập nhật') ...[
                      const SizedBox(width: 6),
                      const Icon(Icons.copy, size: 13, color: AppColors.brand),
                    ],
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 20, color: AppColors.hair),
          _buildInfoRow(Icons.email_outlined, 'Email Phụ huynh', p.parentEmail),
        ],
      ),
    );
  }

  Widget _buildAttendanceStatsSection() {
    final stats = _profile!.stats;
    return _buildCardWrapper(
      title: 'THỐNG KÊ ĐIỂM DANH & VẮNG HỌC',
      child: Column(
        children: [
          Row(
            children: [
              _buildStatBox('Tổng số buổi', stats.totalSessions.toString(), AppColors.navy),
              const SizedBox(width: 8),
              _buildStatBox('Có mặt', stats.attendedSessions.toString(), const Color(0xFF137A41)),
              const SizedBox(width: 8),
              _buildStatBox('Vắng học', stats.absentSessions.toString(), stats.absentSessions > 0 ? const Color(0xFFDC2626) : AppColors.muted),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Tỷ lệ chuyên cần', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.navy)),
              Text('${stats.attendanceRate}%', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: stats.attendanceRate >= 80 ? const Color(0xFF137A41) : const Color(0xFFDC2626))),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAttentionSection() {
    final score = _profile!.stats.avgAttentionScore;
    Color color;
    String ratingStr;
    if (score >= 80) { color = AppColors.brand; ratingStr = 'Tốt'; }
    else if (score >= 65) { color = const Color(0xFF2563EB); ratingStr = 'Khá'; }
    else if (score >= 50) { color = const Color(0xFFD9822B); ratingStr = 'Trung bình'; }
    else { color = const Color(0xFFDC2626); ratingStr = 'Cần cải thiện'; }

    return _buildCardWrapper(
      title: 'MỨC ĐỘ TẬP TRUNG TRUNG BÌNH',
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Đánh giá tích lũy ($ratingStr)', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.navy)),
              Text('$score%', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: color)),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(value: (score / 100).clamp(0.0, 1.0), minHeight: 10, backgroundColor: AppColors.appBg, valueColor: AlwaysStoppedAnimation<Color>(color)),
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentSessionSection() {
    return _buildCardWrapper(
      title: 'ĐIỂM DANH PHIÊN HỌC HIỆN TẠI',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: const Center(child: Text('Có mặt')),
                  selected: _currentPresent,
                  selectedColor: const Color(0xFFDCFCE7),
                  labelStyle: TextStyle(fontWeight: FontWeight.bold, color: _currentPresent ? const Color(0xFF16A34A) : AppColors.muted),
                  onSelected: (val) { if (val) setState(() => _currentPresent = true); },
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ChoiceChip(
                  label: const Center(child: Text('Vắng mặt')),
                  selected: !_currentPresent,
                  selectedColor: const Color(0xFFFEE2E2),
                  labelStyle: TextStyle(fontWeight: FontWeight.bold, color: !_currentPresent ? const Color(0xFFDC2626) : AppColors.muted),
                  onSelected: (val) { if (val) setState(() { _currentPresent = false; _currentDistracted = false; }); },
                ),
              ),
            ],
          ),
          if (_currentPresent) ...[
            const SizedBox(height: 12),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              dense: true,
              title: const Text('Mất tập trung trong phiên này'),
              value: _currentDistracted,
              activeColor: const Color(0xFFD9822B),
              onChanged: (val) => setState(() => _currentDistracted = val ?? false),
            ),
          ],
          const SizedBox(height: 12),
          const Text('Ghi chú của giáo viên:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.navy)),
          const SizedBox(height: 6),
          TextFormField(
            controller: _noteController,
            maxLines: 2,
            decoration: InputDecoration(
              hintText: 'Nhập lý do vắng hoặc ghi chú sức khỏe, ý thức...',
              hintStyle: const TextStyle(fontSize: 12, color: Colors.black38),
              filled: true,
              fillColor: AppColors.appBg,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              contentPadding: const EdgeInsets.all(12),
            ),
            style: const TextStyle(fontSize: 13, color: AppColors.navy),
          ),
        ],
      ),
    );
  }

  Widget _buildCardWrapper({required String title, Widget? trailingWidget, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.hair)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.muted, letterSpacing: 0.5)),
              if (trailingWidget != null) trailingWidget,
            ],
          ),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _buildStatBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(color: AppColors.appBg, borderRadius: BorderRadius.circular(10)),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.muted),
        const SizedBox(width: 10),
        Text(label, style: const TextStyle(fontSize: 13, color: AppColors.muted)),
        const Spacer(),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.navy)),
      ],
    );
  }
}
