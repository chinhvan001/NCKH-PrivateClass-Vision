import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/models/class_model.dart';
import '../widgets/class_card.dart';
import '../../class_detail/screens/class_detail_screen.dart';

// Import file chi tiết lớp học của bạn vào đây
// import '../../class_detail/screens/class_detail_screen.dart';

const List<String> filters = ['Tất cả', 'Khối 12', 'Khối 11', 'Khối 10'];

// ==========================================
// MÀN HÌNH CLASSES (LỚP HỌC)
// ==========================================
class ClassesScreen extends StatefulWidget {
  final Function(String id)? onOpenClass;

  const ClassesScreen({super.key, this.onOpenClass});

  @override
  State<ClassesScreen> createState() => _ClassesScreenState();
}

class _ClassesScreenState extends State<ClassesScreen> {
  String _query = '';
  String _filter = 'Tất cả';

  // Lọc danh sách
  List<ClassModel> get _filteredList {
    return mockClasses.where((c) {
      final q = _query.trim().toLowerCase();
      final matchQ =
          q.isEmpty ||
          c.name.toLowerCase().contains(q) ||
          c.id.toLowerCase().contains(q);
      final matchF = _filter == 'Tất cả' || (c.grade.contains(_filter));
      return matchQ && matchF;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          _buildHeader(),
          _buildFilterChips(),
          Expanded(child: _buildClassList()),
        ],
      ),
    );
  }

  // --- CÁC HÀM BUILD GIAO DIỆN CON ---

  Widget _buildHeader() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 12),
      child: Column(
        children: [
          // Row 1: Back + Title + Badge
          Row(
            children: [
              InkWell(
                onTap: () {
                  Navigator.pop(context);
                },
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(shape: BoxShape.circle),
                  child: const Icon(
                    Icons.arrow_back,
                    color: AppColors.navy,
                    size: 22,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'Lớp học',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppColors.navy,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${mockClasses.length} lớp',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: AppColors.brand,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Row 2: Search Box
          Row(
            children: [
              Expanded(
                child: Container(
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.appBg,
                    border: Border.all(color: AppColors.hair),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
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
                          onChanged: (value) => setState(() => _query = value),
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.navy,
                          ),
                          decoration: const InputDecoration(
                            hintText: 'Tìm lớp học...',
                            hintStyle: TextStyle(color: Colors.black38),
                            border: InputBorder.none,
                            isDense: true,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    return Container(
      width: double.infinity,
      color: Colors.white,
      padding: const EdgeInsets.only(bottom: 12),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: filters.map((f) {
            final isSelected = _filter == f;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: InkWell(
                onTap: () => setState(() => _filter = f),
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.navy : AppColors.appBg,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    f,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Colors.white : AppColors.muted,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildClassList() {
    final list = _filteredList;

    if (list.isEmpty) {
      return const Padding(
        padding: EdgeInsets.only(top: 64),
        child: Text(
          'Không tìm thấy lớp học phù hợp.',
          style: TextStyle(fontSize: 14, color: AppColors.muted),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final c = list[index];

        // Component xử lý điều hướng cho từng Card
        final cardWidget = ClassCard(
          classInfo: c,
          onTap: () {
            if (widget.onOpenClass != null) {
              widget.onOpenClass!(c.id);
            }
            // Gọi màn hình ClassDetailScreen tại đây
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ClassDetailScreen(classId: c.id),
              ),
            );
          },
        );

        // Thêm tiêu đề ở phần tử đầu tiên
        if (index == 0) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(left: 4, bottom: 8),
                child: Text(
                  'Danh sách lớp đang dạy',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: AppColors.navy,
                  ),
                ),
              ),
              cardWidget,
            ],
          );
        }

        return cardWidget;
      },
    );
  }
}
