import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class AttendanceDetailScreen extends StatefulWidget {
  const AttendanceDetailScreen({super.key});

  @override
  State<AttendanceDetailScreen> createState() => _AttendanceDetailScreenState();
}

class _AttendanceDetailScreenState extends State<AttendanceDetailScreen> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  String _selectedPeriod = 'Học kỳ 1';
  final List<String> _periods = ['Học kỳ 1', 'Học kỳ 2', 'Cả năm', 'Tháng này'];

  Future<AttendanceSummary>? _summaryFuture;
  String? _lastLoadedStudentId;

  @override
  void initState() {
    super.initState();
    _fetchAttendance();
  }

  void _fetchAttendance() {
    final currentChild = _session.selectedChild;
    if (currentChild != null) {
      _lastLoadedStudentId = currentChild.id;
      final classId = currentChild.classes.isNotEmpty ? currentChild.classes.first.id : null;
      setState(() {
        _summaryFuture = _parentService.getAttendanceSummary(
          studentId: currentChild.id,
          classId: classId,
          period: _selectedPeriod,
        );
      });
    } else {
      setState(() {
        _summaryFuture = Future.value(const AttendanceSummary());
      });
    }
  }

  void _onPeriodChanged(String period) {
    if (_selectedPeriod == period) return;
    setState(() {
      _selectedPeriod = period;
    });
    _fetchAttendance();
  }

  @override
  Widget build(BuildContext context) {
    final currentChild = _session.selectedChild;

    if (currentChild != null && currentChild.id != _lastLoadedStudentId) {
      _fetchAttendance();
    }

    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios,
            color: AppColors.textPrimary,
            size: 20,
          ),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Chi tiết điểm danh', style: AppTextStyles.heading2),
      ),
      body: currentChild == null
          ? const Center(child: Text('Chưa có thông tin học sinh'))
          : RefreshIndicator(
              onRefresh: () async => _fetchAttendance(),
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header học sinh + Tên kỳ đang chọn
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.school_rounded, color: AppColors.primary, size: 20),
                              const SizedBox(width: 8),
                              Text(
                                _selectedPeriod,
                                style: AppTextStyles.heading3.copyWith(color: AppColors.primary),
                              ),
                            ],
                          ),
                          Text(
                            currentChild.shortName,
                            style: AppTextStyles.body2.copyWith(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Thanh nút bấm lọc theo kỳ
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.divider),
                        ),
                        child: Row(
                          children: _periods.map((p) {
                            final selected = p == _selectedPeriod;
                            return GestureDetector(
                              onTap: () => _onPeriodChanged(p),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 7,
                                ),
                                decoration: BoxDecoration(
                                  color: selected ? AppColors.primary : Colors.transparent,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  p,
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                    color: selected ? Colors.white : AppColors.textSecondary,
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    FutureBuilder<AttendanceSummary>(
                      future: _summaryFuture,
                      builder: (context, snapshot) {
                        if (snapshot.connectionState == ConnectionState.waiting) {
                          return const Padding(
                            padding: EdgeInsets.symmetric(vertical: 40),
                            child: Center(child: CircularProgressIndicator()),
                          );
                        }

                        if (snapshot.hasError) {
                          return Center(child: Text('Lỗi tải dữ liệu: ${snapshot.error}'));
                        }

                        final summary = snapshot.data ?? const AttendanceSummary();

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            AppCard(
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceAround,
                                children: [
                                  _SummaryBox(
                                    label: 'Tổng số buổi',
                                    value: summary.totalSessions.toString(),
                                    color: AppColors.textPrimary,
                                  ),
                                  Container(width: 1, height: 40, color: AppColors.divider),
                                  _SummaryBox(
                                    label: 'Đã tham gia',
                                    value: summary.attendedSessions.toString(),
                                    color: AppColors.green,
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 10),
                            AppCard(
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.spaceAround,
                                children: [
                                  _SummaryBox(
                                    label: 'Vắng có phép',
                                    value: summary.excusedAbsences.toString(),
                                    color: AppColors.orange,
                                  ),
                                  Container(width: 1, height: 40, color: AppColors.divider),
                                  _SummaryBox(
                                    label: 'Vắng không phép',
                                    value: summary.unexcusedAbsences.toString(),
                                    color: AppColors.red,
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 10),
                            AppCard(
                              child: _SummaryBox(
                                label: 'Đi muộn',
                                value: summary.lateSessions.toString(),
                                color: AppColors.primary,
                              ),
                            ),
                            const SizedBox(height: 16),
                            const Text('Danh sách vắng & ghi chú', style: AppTextStyles.heading3),
                            const SizedBox(height: 10),
                            if (summary.absenceList.isEmpty)
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 20),
                                child: Center(
                                  child: Text(
                                    'Không có ghi nhận vắng trong khoảng thời gian này',
                                    style: AppTextStyles.caption,
                                  ),
                                ),
                              )
                            else
                              ...summary.absenceList.map(
                                (a) => Padding(
                                  padding: const EdgeInsets.only(bottom: 10),
                                  child: AppCard(
                                    child: Row(
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.all(10),
                                          decoration: BoxDecoration(
                                            color: a.type == 'Đi muộn'
                                                ? AppColors.primaryLight
                                                : AppColors.orangeLight,
                                            shape: BoxShape.circle,
                                          ),
                                          child: Icon(
                                            a.type == 'Đi muộn' ? Icons.alarm : Icons.event_busy,
                                            color: a.type == 'Đi muộn'
                                                ? AppColors.primary
                                                : AppColors.orange,
                                            size: 20,
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(a.date, style: AppTextStyles.caption),
                                              const SizedBox(height: 3),
                                              Text(
                                                a.type,
                                                style: AppTextStyles.body2.copyWith(
                                                  fontWeight: FontWeight.w600,
                                                  color: a.type == 'Đi muộn'
                                                      ? AppColors.primary
                                                      : AppColors.orange,
                                                ),
                                              ),
                                              const SizedBox(height: 2),
                                              Text(a.reason, style: AppTextStyles.caption),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}

class _SummaryBox extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _SummaryBox({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: AppTextStyles.caption),
      ],
    );
  }
}