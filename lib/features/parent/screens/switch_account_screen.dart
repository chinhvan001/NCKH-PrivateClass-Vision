import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class SwitchAccountScreen extends StatefulWidget {
  const SwitchAccountScreen({super.key});

  @override
  State<SwitchAccountScreen> createState() => _SwitchAccountScreenState();
}

class _SwitchAccountScreenState extends State<SwitchAccountScreen> {
  int _selectedIndex = 0;

  final List<Map<String, dynamic>> _children = [
    {
      'name': 'Minh Anh',
      'class': 'Lớp 5A - Trường Tiểu học ABC',
    },
    {
      'name': 'Gia Hưng',
      'class': 'Lớp 2B - Trường Tiểu học ABC',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
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
          // Children list
          ..._children.asMap().entries.map((entry) {
            final i = entry.key;
            final child = entry.value;
            final selected = i == _selectedIndex;
            return GestureDetector(
              onTap: () => setState(() => _selectedIndex = i),
              child: Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: selected ? AppColors.accentLight : AppColors.backgroundGrey,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: selected ? AppColors.primary : Colors.transparent,
                    width: 1.5,
                  ),
                ),
                child: Row(
                  children: [
                    AvatarWidget(
                      name: child['name'] as String,
                      size: 44,
                      bgColor: selected ? AppColors.primary : AppColors.accentLight,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            child['name'] as String,
                            style: AppTextStyles.heading3.copyWith(
                              color: selected ? AppColors.primary : AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(child['class'] as String, style: AppTextStyles.caption),
                        ],
                      ),
                    ),
                    if (selected)
                      const Icon(Icons.check_circle, color: AppColors.primary, size: 22),
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
    );
  }
}
