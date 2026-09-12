import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/child_model.dart';
import '../services/child_service.dart';

class SwitchAccountScreen extends StatefulWidget {
  const SwitchAccountScreen({super.key});

  @override
  State<SwitchAccountScreen> createState() => _SwitchAccountScreenState();
}

class _SwitchAccountScreenState extends State<SwitchAccountScreen> {
  // TODO: thay bằng parentId thật từ auth sau
  static const String _parentId = 'parent_001';

  final _service = ChildService();
  late Future<List<ChildModel>> _childrenFuture;
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _childrenFuture = _service.getChildrenByParent(_parentId);
  }

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
          // ── Handle bar ─────────────────────────────────────────────
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

          // ── Children list ───────────────────────────────────────────
          FutureBuilder<List<ChildModel>>(
            future: _childrenFuture,
            builder: (context, snapshot) {
              // Loading
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: CircularProgressIndicator(
                        color: AppColors.primary),
                  ),
                );
              }

              // Error
              if (snapshot.hasError) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    child: Column(
                      children: [
                        const Icon(Icons.cloud_off_rounded,
                            size: 36, color: AppColors.red),
                        const SizedBox(height: 8),
                        Text(
                          snapshot.error
                              .toString()
                              .replaceFirst('Exception: ', ''),
                          style: AppTextStyles.caption,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 10),
                        TextButton.icon(
                          onPressed: () => setState(() {
                            _childrenFuture =
                                _service.getChildrenByParent(_parentId);
                          }),
                          icon: const Icon(Icons.refresh_rounded,
                              size: 16, color: AppColors.primary),
                          label: const Text('Thử lại',
                              style: AppTextStyles.linkText),
                        ),
                      ],
                    ),
                  ),
                );
              }

              final children = snapshot.data ?? [];

              // Empty
              if (children.isEmpty) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Column(
                      children: [
                        Icon(Icons.person_off_rounded,
                            size: 40, color: AppColors.textHint),
                        SizedBox(height: 8),
                        Text('Chưa có tài khoản con nào',
                            style: AppTextStyles.caption),
                      ],
                    ),
                  ),
                );
              }

              return Column(
                children: children.asMap().entries.map((entry) {
                  final i = entry.key;
                  final child = entry.value;
                  final selected = i == _selectedIndex;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedIndex = i),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: selected
                            ? AppColors.accentLight
                            : AppColors.backgroundGrey,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: selected
                              ? AppColors.primary
                              : Colors.transparent,
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
                                  '${child.className} · ${child.schoolName}',
                                  style: AppTextStyles.caption,
                                ),
                                const SizedBox(height: 3),
                                Row(
                                  children: [
                                    const Icon(Icons.psychology_rounded,
                                        size: 12,
                                        color: AppColors.textSecondary),
                                    const SizedBox(width: 4),
                                    Text(
                                      'Tập trung TB: ${child.avgFocusPercent}%',
                                      style: AppTextStyles.small,
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          if (selected)
                            const Icon(Icons.check_circle_rounded,
                                color: AppColors.primary, size: 22),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              );
            },
          ),

          const SizedBox(height: 20),

          // ── Confirm button ──────────────────────────────────────────
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
              child: const Text('Xác nhận', style: AppTextStyles.buttonText),
            ),
          ),
        ],
      ),
    );
  }
}
