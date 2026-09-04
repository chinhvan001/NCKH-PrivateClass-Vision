import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../../core/data/mock_homeroom.dart';

class SeatingMatrix extends StatelessWidget {
  final int rows;
  final int cols;
  final List<String?> seats;
  final bool isEdit;
  final int? selectedCell;
  final Function(int)? onTapCell;

  const SeatingMatrix({
    super.key,
    required this.rows,
    required this.cols,
    required this.seats,
    this.isEdit = false,
    this.selectedCell,
    this.onTapCell,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Sơ đồ lớp',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: AppColors.navy,
              ),
            ),
            Text(
              '$rows × $cols vị trí',
              style: const TextStyle(fontSize: 12, color: AppColors.muted),
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
                    final studentId = seats[index];
                    final student = studentId != null
                        ? homeroomRoster.firstWhere((s) => s.id == studentId)
                        : null;
                    final isSel = selectedCell == index;

                    Color bgColor = AppColors.appBg;
                    Color borderColor = AppColors.hair;
                    Widget content = const SizedBox();

                    if (student != null) {
                      bgColor = isSel
                          ? AppColors.lightBlue
                          : AppColors.lightBlue.withOpacity(0.5);
                      borderColor = isSel ? AppColors.brand : AppColors.hair;
                      content = Text(
                        student.short,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: AppColors.navy,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      );
                    } else if (isEdit) {
                      bgColor = selectedCell != null
                          ? AppColors.lightBlue.withOpacity(0.2)
                          : Colors.white;
                      borderColor = AppColors.brand.withOpacity(0.4);
                      content = const Icon(
                        Icons.add,
                        size: 14,
                        color: AppColors.brand,
                      );
                    }

                    return InkWell(
                      onTap: isEdit ? () => onTapCell?.call(index) : null,
                      child: Container(
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: bgColor,
                          border: Border.all(color: borderColor),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: content,
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
}
