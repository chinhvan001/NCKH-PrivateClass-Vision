import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';

// Đã thêm trường "status" vào dữ liệu để phân biệt trạng thái phiên
class HistItem {
  final String id, classId, className, room, date, start, end, status;
  final int size;

  const HistItem({
    required this.id,
    required this.classId,
    required this.className,
    required this.room,
    required this.date,
    required this.start,
    required this.end,
    required this.size,
    required this.status,
  });
}

class SessionListCard extends StatelessWidget {
  final HistItem item;
  final VoidCallback onTap;

  const SessionListCard({super.key, required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    Color statusBgColor;

    // Thiết lập màu sắc theo trạng thái
    switch (item.status) {
      case 'Đang diễn ra':
        statusColor = const Color(0xFF137A41);
        statusBgColor = const Color(0xFFE9F8EF);
        break;
      case 'Sắp diễn ra':
        statusColor = AppColors.brand;
        statusBgColor = AppColors.lightBlue.withOpacity(0.5);
        break;
      default: // Đã kết thúc
        statusColor = AppColors.muted;
        statusBgColor = AppColors.appBg;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.hair),
        ),
        color: Colors.white,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Khung Gradient chứa mã lớp
                Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    gradient: item.status == 'Đã kết thúc'
                        ? const LinearGradient(
                            colors: [Colors.grey, Colors.black26],
                          )
                        : const LinearGradient(
                            colors: [AppColors.brand, Color(0xFF1D4ED8)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    item.classId,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                // Cột nội dung
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${item.className} · Phòng ${item.room}',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: item.status == 'Đã kết thúc'
                              ? AppColors.muted
                              : AppColors.navy,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 14,
                        runSpacing: 4,
                        children: [
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.schedule,
                                size: 13,
                                color: AppColors.muted,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${item.start}–${item.end}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.muted,
                                ),
                              ),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.people_alt_outlined,
                                size: 13,
                                color: AppColors.muted,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${item.size} HS',
                                style: const TextStyle(
                                  fontSize: 12,
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
                // Badge Trạng thái thay cho icon mũi tên
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: statusBgColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    item.status,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
