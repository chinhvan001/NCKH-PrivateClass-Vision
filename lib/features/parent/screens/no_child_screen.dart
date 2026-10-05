import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/auth/controllers/active_role.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

/// Hiển thị khi tài khoản phụ huynh chưa được liên kết với học sinh nào,
/// hoặc khi tải danh sách con bị lỗi.
class NoChildScreen extends StatelessWidget {
  final String? errorMessage;
  final VoidCallback onRetry;

  const NoChildScreen({super.key, this.errorMessage, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final hasError = errorMessage != null;

    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 88,
                  height: 88,
                  decoration: BoxDecoration(
                    color: hasError ? AppColors.redLight : AppColors.accentLight,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    hasError ? Icons.cloud_off_rounded : Icons.link_off_rounded,
                    color: hasError ? AppColors.red : AppColors.primary,
                    size: 44,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  hasError ? 'Không tải được dữ liệu' : 'Chưa liên kết học sinh',
                  style: AppTextStyles.heading2,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  hasError
                      ? 'Vui lòng kiểm tra kết nối mạng rồi thử lại.\n$errorMessage'
                      : 'Tài khoản của bạn chưa được liên kết với học sinh nào.\n'
                          'Vui lòng liên hệ giáo viên để được thêm vào danh sách phụ huynh.',
                  style: AppTextStyles.body2,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 28),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: onRetry,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('Thử lại', style: AppTextStyles.buttonText),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: OutlinedButton(
                    onPressed: () => signOutAndResetRole(),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.red,
                      side: const BorderSide(color: AppColors.red),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('Đăng xuất'),
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
