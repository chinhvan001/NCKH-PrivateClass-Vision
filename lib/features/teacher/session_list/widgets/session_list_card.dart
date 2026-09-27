import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
// Thay đổi đường dẫn import này cho khớp với vị trí file SessionModel.dart của bạn nếu cần
import '../../../../core/models/session_model.dart';

class SessionListCard extends StatelessWidget {
  final SessionModel item; // Đã đổi từ HistItem sang SessionModel
  final VoidCallback onTap;

  const SessionListCard({super.key, required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    Color statusBgColor;

    // Thiết lập màu sắc theo trạng thái
    // Lưu ý: Đảm bảo dữ liệu 'status' lưu trên Firebase khớp với các chuỗi này
    // (ví dụ: 'Đang diễn ra', 'Sắp diễn ra', 'Đã kết thúc')
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
                    gradient: const LinearGradient(
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
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: AppColors.navy,
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
                // Badge Trạng thái
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
