import 'package:flutter/material.dart';

import '../core/constants/app_colors.dart';

class ActionRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? hint;

  const ActionRow({
    super.key,
    required this.icon,
    required this.label,
    this.hint,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {},
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.lightBlue,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: AppColors.brand, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.navy,
                ),
              ),
            ),
            if (hint != null) ...[
              Text(
                hint!,
                style: const TextStyle(fontSize: 12, color: AppColors.muted),
              ),
              const SizedBox(width: 8),
            ],
            const Icon(Icons.chevron_right, size: 20, color: Colors.black26),
          ],
        ),
      ),
    );
  }
}
