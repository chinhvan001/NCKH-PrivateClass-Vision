import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';

// Status badge chip
class StatusChip extends StatelessWidget {
  final String label;
  final Color bgColor;
  final Color textColor;
  final double fontSize;

  const StatusChip({
    super.key,
    required this.label,
    required this.bgColor,
    required this.textColor,
    this.fontSize = 11,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.w600,
          color: textColor,
        ),
      ),
    );
  }
}

// Card container
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final double? borderRadius;
  final Color? color;
  final VoidCallback? onTap;

  const AppCard({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius,
    this.color,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: padding ?? const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color ?? AppColors.cardWhite,
          borderRadius: BorderRadius.circular(borderRadius ?? 12),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0F000000),
              blurRadius: 6,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: child,
      ),
    );
  }
}

// Section header with title and optional action
class SectionHeader extends StatelessWidget {
  final String title;
  final String? actionText;
  final VoidCallback? onAction;

  const SectionHeader({
    super.key,
    required this.title,
    this.actionText,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: AppTextStyles.heading3),
        if (actionText != null)
          GestureDetector(
            onTap: onAction,
            child: Text(actionText!, style: AppTextStyles.linkText),
          ),
      ],
    );
  }
}

// Circular progress with label
class CircularProgressWidget extends StatelessWidget {
  final double percent;
  final String centerText;
  final String label;
  final Color color;
  final double size;

  const CircularProgressWidget({
    super.key,
    required this.percent,
    required this.centerText,
    required this.label,
    required this.color,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator(
                  value: percent / 100,
                  strokeWidth: 7,
                  backgroundColor: AppColors.divider,
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              ),
              Text(
                centerText,
                style: TextStyle(
                  fontSize: size * 0.18,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text(label, style: AppTextStyles.caption),
      ],
    );
  }
}

// Linear progress bar with label and percent
class SubjectProgressBar extends StatelessWidget {
  final String subject;
  final int percent;
  final Color color;

  const SubjectProgressBar({
    super.key,
    required this.subject,
    required this.percent,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(subject, style: AppTextStyles.body2),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: percent / 100,
                minHeight: 8,
                backgroundColor: AppColors.divider,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text('$percent%', style: AppTextStyles.body2),
        ],
      ),
    );
  }
}

// Notification badge icon
class BadgeIcon extends StatelessWidget {
  final IconData icon;
  final int count;

  const BadgeIcon({super.key, required this.icon, required this.count});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Icon(icon, color: AppColors.textPrimary, size: 26),
        if (count > 0)
          Positioned(
            right: 0,
            top: 0,
            child: Container(
              width: 16,
              height: 16,
              decoration: const BoxDecoration(
                color: AppColors.red,
                shape: BoxShape.circle,
              ),
              child: Center(
                child: Text(
                  '$count',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

// Avatar circle with initials
class AvatarWidget extends StatelessWidget {
  final String name;
  final double size;
  final Color bgColor;

  const AvatarWidget({
    super.key,
    required this.name,
    this.size = 40,
    this.bgColor = AppColors.accentLight,
  });

  String get _initials {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[parts.length - 1][0]}'.toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: bgColor,
        shape: BoxShape.circle,
      ),
      child: Center(
        child: Text(
          _initials,
          style: TextStyle(
            fontSize: size * 0.35,
            fontWeight: FontWeight.bold,
            color: AppColors.primary,
          ),
        ),
      ),
    );
  }
}
