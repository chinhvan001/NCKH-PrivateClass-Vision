import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class SwitchAccountScreen extends StatelessWidget {
  const SwitchAccountScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final session = ParentSession.instance;

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: ListenableBuilder(
        listenable: session,
        builder: (context, _) => Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text('Chọn tài khoản con', style: AppTextStyles.heading2),
            const SizedBox(height: 16),
            // Children list (students có parent_id = uid phụ huynh)
            ...session.children.map((child) {
              final selected = child.id == session.selectedChild?.id;
              return GestureDetector(
                onTap: () => session.selectChild(child),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: selected
                        ? AppColors.accentLight
                        : AppColors.backgroundGrey,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: selected ? AppColors.primary : Colors.transparent,
                      width: 1.5,
                    ),
                  ),
                  child: Row(
                    children: [
                      AvatarWidget(
                        name: child.name,
                        size: 44,
                        bgColor: selected
                            ? AppColors.primary
                            : AppColors.accentLight,
                        textColor: selected ? Colors.white : AppColors.primary,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              child.name,
                              style: AppTextStyles.heading3.copyWith(
                                color: selected
                                    ? AppColors.primary
                                    : AppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              child.classDisplay,
                              style: AppTextStyles.caption,
                            ),
                          ],
                        ),
                      ),
                      if (selected)
                        const Icon(
                          Icons.check_circle,
                          color: AppColors.primary,
                          size: 22,
                        ),
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 20),
            // Close button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Đóng', style: AppTextStyles.buttonText),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
