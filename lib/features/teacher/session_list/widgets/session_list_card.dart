import 'package:flutter/material.dart';
import '../../../../../core/constants/app_colors.dart';

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

    switch (item.status) {
      case 'Đang diễn ra':
        statusColor = const Color(0xFF137A41);
        statusBgColor = const Color(0xFFE9F8EF);
        break;
      case 'Sắp diễn ra':
        statusColor = AppColors.brand;
        statusBgColor = AppColors.lightBlue.withValues(alpha: 0.5);
        break;
      default: // Đã kết thúc
        statusColor = AppColors.muted;
        statusBgColor = AppColors.appBg;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
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
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // 1. Icon / Mã lớp
                Container(
                  width: 40,
                  height: 40,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    gradient: 
                        const LinearGradient(
                            colors: [AppColors.brand, Color(0xFF1D4ED8)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    item.className.length > 4 
                        ? item.className.substring(0, 4) 
                        : item.className,
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(width: 10),

                // 2. Nội dung chính (Sử dụng Wrap linh hoạt tự điều chỉnh vị trí)
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Tên lớp học
                      Text(
                        item.className,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: item.status == 'Đã kết thúc'
                              ? AppColors.muted
                              : AppColors.navy,
                        ),
                      ),
                      const SizedBox(height: 4),

                      // Thông tin chi tiết: Phòng - Giờ - Sĩ số (Dùng Wrap thay vì SingleChildScrollView)
                      Wrap(
                        spacing: 6,
                        runSpacing: 2,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          _buildInfoBadge(
                            Icons.meeting_room_outlined,
                            item.room,
                          ),
                          _buildInfoBadge(
                            Icons.schedule,
                            '${item.start}–${item.end}',
                          ),
                          _buildInfoBadge(
                            Icons.people_alt_outlined,
                            '${item.size}',
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),

                // 3. Badge Trạng thái
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: statusBgColor,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    item.status,
                    style: TextStyle(
                      fontSize: 9.5,
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

  // Widget con hiển thị từng thông tin gọn gàng
  Widget _buildInfoBadge(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 11, color: AppColors.muted),
        const SizedBox(width: 2),
        Text(
          text,
          style: const TextStyle(
            fontSize: 10.5,
            color: AppColors.muted,
          ),
        ),
      ],
    );
  }
}