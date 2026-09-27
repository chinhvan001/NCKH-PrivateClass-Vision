import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../controllers/class_detail_controller.dart';
import '../widgets/class_stats_card.dart';
import '../widgets/seating_chart_widget.dart';
import '../widgets/session_schedule_widget.dart';
import '../widgets/student_list_widget.dart';

class ClassDetailScreen extends StatefulWidget {
  final String classId;

  const ClassDetailScreen({super.key, required this.classId});

  @override
  State<ClassDetailScreen> createState() => _ClassDetailScreenState();
}

class _ClassDetailScreenState extends State<ClassDetailScreen> {
  late final ClassDetailController _controller;
  final List<String> _tabs = ['Lịch dạy', 'Học sinh', 'Sơ đồ lớp'];
  final List<IconData> _tabIcons = [
    Icons.calendar_today_rounded,
    Icons.people_alt_rounded,
    Icons.grid_view_rounded,
  ];
  int _selectedTabIndex = 0;

  @override
  void initState() {
    super.initState();
    _controller = ClassDetailController(classId: widget.classId);
    _selectedTabIndex = _controller.selectedTabIndex;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTabTapped(int index) {
    if (_selectedTabIndex != index) {
      setState(() {
        _selectedTabIndex = index;
      });
      _controller.setTabIndex(index);
    }
  }


  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Scaffold(
          backgroundColor: AppColors.appBg,
          body: Column(
            children: [
              _buildHeader(context),
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
                    child: _buildBody(context),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeader(BuildContext context) {
    final title = _controller.classDetail?.name ?? 'Chi tiết lớp học';
    final room = _controller.classroomName;
    final size = _controller.classDetail?.students ?? _controller.totalEnrolled;
    final topPadding = MediaQuery.of(context).padding.top;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(16, topPadding + 12, 16, 28),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.navy, AppColors.darkBlue],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Row(
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => Navigator.pop(context),
              borderRadius: BorderRadius.circular(20),
              child: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.14),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.2),
                    width: 1,
                  ),
                ),
                child: const Icon(Icons.arrow_back, color: Colors.white, size: 20),
              ),
            ),
          ),
          const SizedBox(width: 14),
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
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.16),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        'Phòng $room',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '$size học sinh',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Colors.white.withValues(alpha: 0.8),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => _controller.refresh(),
              borderRadius: BorderRadius.circular(20),
              child: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.14),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.2),
                    width: 1,
                  ),
                ),
                child: const Icon(Icons.refresh, color: Colors.white, size: 20),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (_controller.isLoading) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: AppColors.brand),
            SizedBox(height: 12),
            Text(
              'Đang tải dữ liệu lớp học...',
              style: TextStyle(fontSize: 13, color: AppColors.muted),
            ),
          ],
        ),
      );
    }

    if (_controller.hasError) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
              const SizedBox(height: 12),
              Text(
                _controller.errorMessage ?? 'Đã có lỗi xảy ra',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.redAccent, fontSize: 14),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => _controller.refresh(),
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Thử lại'),
              ),
            ],
          ),
        ),
      );
    }

    if (!_controller.hasData) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.class_outlined, size: 48, color: AppColors.muted),
            const SizedBox(height: 12),
            const Text(
              'Không tìm thấy lớp học.',
              style: TextStyle(fontSize: 14, color: AppColors.muted),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Quay lại'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _controller.refresh,
      color: AppColors.brand,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClassStatsCard(controller: _controller),
            const SizedBox(height: 16),
            _buildTabBar(),
            const SizedBox(height: 16),
            _buildTabContent(),
          ],
        ),
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFFE2E8F0),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: List.generate(_tabs.length, (index) {
          final isSelected = _selectedTabIndex == index;
          return Expanded(
            child: GestureDetector(
              onTap: () => _onTabTapped(index),
              behavior: HitTestBehavior.opaque,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 9),
                decoration: BoxDecoration(
                  color: isSelected ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(9),
                  boxShadow: isSelected
                      ? [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.08),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : null,
                ),
                alignment: Alignment.center,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _tabIcons[index],
                      size: 14,
                      color: isSelected ? AppColors.navy : AppColors.muted,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      _tabs[index],
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                        color: isSelected ? AppColors.navy : AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_selectedTabIndex) {
      case 0:
        return SessionScheduleWidget(controller: _controller);
      case 1:
        return StudentListWidget(controller: _controller);
      case 2:
        return SeatingChartWidget(controller: _controller);
      default:
        return const SizedBox.shrink();
    }
  }
}
