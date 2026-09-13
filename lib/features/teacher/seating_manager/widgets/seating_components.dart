import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';

// 1. Thẻ hiển thị Sĩ số / Đã xếp chỗ (Dùng ở cả chế độ View và Edit)
class CountCard extends StatelessWidget {
  final int assignedCount;
  final int totalSize;

  const CountCard({
    super.key,
    required this.assignedCount,
    required this.totalSize,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Sĩ số lớp',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
                Text(
                  '$totalSize học sinh',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AppColors.navy,
                  ),
                ),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const Text(
                  'Đã xếp chỗ',
                  style: TextStyle(fontSize: 12, color: AppColors.muted),
                ),
                Text(
                  '$assignedCount/$totalSize',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AppColors.brand,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// 2. Thẻ Thông tin Lớp học (Dùng ở chế độ View)
class HomeroomInfoCard extends StatelessWidget {
  final Map<String, Object> info;

  const HomeroomInfoCard({super.key, required this.info});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
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
                info['id'].toString(),
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
                  Text(
                    info['name'].toString(),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppColors.navy,
                    ),
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
                            'Phòng ${info['room']}',
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
                            Icons.people_alt_outlined,
                            size: 15,
                            color: AppColors.muted,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '${info['size']} học sinh',
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
      ),
    );
  }
}