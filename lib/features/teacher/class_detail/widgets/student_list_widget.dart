import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/student_model.dart';
import '../controllers/class_detail_controller.dart';

class StudentListWidget extends StatelessWidget {
  final ClassDetailController controller;
  const StudentListWidget({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final students = controller.filteredStudents;

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.hair),
          ),
          child: TextField(
            onChanged: controller.setSearchStudentQuery,
            decoration: const InputDecoration(
              icon: Icon(Icons.search, color: AppColors.muted, size: 20),
              hintText: 'Tìm kiếm tên hoặc email...',
              hintStyle: TextStyle(fontSize: 13, color: AppColors.muted),
              border: InputBorder.none,
              isDense: true,
              contentPadding: EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Danh sách (${students.length} học sinh)',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: AppColors.navy,
              ),
            ),
            if (controller.searchStudentQuery.isNotEmpty)
              GestureDetector(
                onTap: () => controller.setSearchStudentQuery(''),
                child: const Text(
                  'Xóa tìm kiếm',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.brand,
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        if (students.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.hair),
            ),
            child: Column(
              children: [
                const Icon(Icons.people_outline, size: 40, color: AppColors.muted),
                const SizedBox(height: 8),
                Text(
                  controller.searchStudentQuery.isNotEmpty
                      ? 'Không tìm thấy học sinh phù hợp.'
                      : 'Chưa có học sinh nào trong lớp học.',
                  style: const TextStyle(fontSize: 13, color: AppColors.muted),
                ),
              ],
            ),
          )
        else
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: students.length,
            separatorBuilder: (context, index) => const SizedBox(height: 8),
            itemBuilder: (context, index) => _item(students[index], index + 1),
          ),
      ],
    );
  }

  Widget _item(StudentModel s, int idx) {
    final hasSeat = s.row != null && s.row! > 0 && s.column != null && s.column! > 0;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.hair),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: AppColors.lightBlue,
            child: Text(
              s.short.isNotEmpty ? s.short : '$idx',
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: AppColors.brand,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.navy,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  hasSeat
                      ? 'Hàng ${s.row}, Cột ${s.column}'
                      : 'Chưa xếp chỗ ngồi',
                  style: TextStyle(
                    fontSize: 12,
                    color: hasSeat ? AppColors.brand : AppColors.muted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
