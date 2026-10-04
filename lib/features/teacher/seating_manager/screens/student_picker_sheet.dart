import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../../core/models/student_model.dart';

/// Mở bottom sheet để chọn một học sinh gán vào ô ghế trống.
/// Gọi [onSelect] với học sinh được chọn rồi tự đóng sheet.
Future<void> showStudentPickerSheet(
  BuildContext context, {
  required List<StudentModel> unassignedStudents,
  required void Function(StudentModel student) onSelect,
}) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (context) => _StudentPickerSheet(
      unassignedStudents: unassignedStudents,
      onSelect: onSelect,
    ),
  );
}

class _StudentPickerSheet extends StatefulWidget {
  const _StudentPickerSheet({
    required this.unassignedStudents,
    required this.onSelect,
  });

  final List<StudentModel> unassignedStudents;
  final void Function(StudentModel student) onSelect;

  @override
  State<_StudentPickerSheet> createState() => _StudentPickerSheetState();
}

class _StudentPickerSheetState extends State<_StudentPickerSheet> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final filtered = widget.unassignedStudents
        .where((s) => s.name.toLowerCase().contains(_query.trim().toLowerCase()))
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
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.navy),
              ),
              Text(
                'Còn ${widget.unassignedStudents.length} chưa xếp',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.muted),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildSearchField(),
          const SizedBox(height: 16),
          Expanded(child: _buildList(filtered)),
        ],
      ),
    );
  }

  Widget _buildSearchField() {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: AppColors.appBg,
        border: Border.all(color: AppColors.hair),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.search, color: AppColors.muted, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: TextField(
              onChanged: (val) => setState(() => _query = val),
              decoration: const InputDecoration(
                hintText: 'Tìm học sinh...',
                hintStyle: TextStyle(color: Colors.black38),
                border: InputBorder.none,
                isDense: true,
              ),
              style: const TextStyle(fontSize: 14, color: AppColors.navy),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildList(List<StudentModel> list) {
    if (list.isEmpty) {
      return const Center(
        child: Text(
          'Đã xếp chỗ cho tất cả hoặc không tìm thấy.',
          style: TextStyle(fontSize: 14, color: AppColors.muted),
        ),
      );
    }

    return ListView.builder(
      itemCount: list.length,
      itemBuilder: (context, index) {
        final s = list[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: InkWell(
            onTap: () {
              widget.onSelect(s);
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
                      s.short.isNotEmpty ? s.short[0] : 'S',
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      s.name,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.navy),
                    ),
                  ),
                  const Icon(Icons.add, color: AppColors.brand, size: 20),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
