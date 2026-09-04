import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';


class AppBottomNavBar extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const AppBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  static const _items = [
    _NavItem(
      icon: Icons.home_outlined,
      activeIcon: Icons.home_rounded,
      label: 'Trang chủ',
    ),
    _NavItem(
      icon: Icons.history_outlined,
      activeIcon: Icons.history_rounded,
      label: 'Lịch sử',
    ),
    _NavItem(
      icon: Icons.notifications_none_rounded,
      activeIcon: Icons.notifications_rounded,
      label: 'Thông báo',
    ),
    _NavItem(
      icon: Icons.person_outline_rounded,
      activeIcon: Icons.person_rounded,
      label: 'Hồ sơ',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Color(0x18000000),
            blurRadius: 16,
            offset: Offset(0, -3),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 64,
          child: Row(
            children: List.generate(_items.length, (i) {
              final selected = i == currentIndex;
              return Expanded(
                child: _NavButton(
                  item: _items[i],
                  selected: selected,
                  onTap: () => onTap(i),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

// ─── Data class ────────────────────────────────────────────────────────────────
class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  const _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}

// ─── Animated nav button ───────────────────────────────────────────────────────
class _NavButton extends StatefulWidget {
  final _NavItem item;
  final bool selected;
  final VoidCallback onTap;

  const _NavButton({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  @override
  State<_NavButton> createState() => _NavButtonState();
}

class _NavButtonState extends State<_NavButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;
  late final Animation<double> _iconScale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
    );
    _scale = Tween<double>(begin: 1.0, end: 0.88).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
    _iconScale = Tween<double>(begin: 1.0, end: 1.18).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.elasticOut),
    );
  }

  @override
  void didUpdateWidget(_NavButton old) {
    super.didUpdateWidget(old);
    if (widget.selected && !old.selected) {
      _ctrl.forward(from: 0).then((_) => _ctrl.reverse());
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      behavior: HitTestBehavior.opaque,
      child: ScaleTransition(
        scale: _scale,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated pill background behind icon
            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeInOut,
              width: selected ? 52 : 36,
              height: 32,
              decoration: BoxDecoration(
                color: selected
                    ? AppColors.primary.withValues(alpha: 0.12)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Center(
                child: ScaleTransition(
                  scale: _iconScale,
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    transitionBuilder: (child, anim) => ScaleTransition(
                      scale: anim,
                      child: FadeTransition(opacity: anim, child: child),
                    ),
                    child: Icon(
                      selected ? widget.item.activeIcon : widget.item.icon,
                      key: ValueKey(selected),
                      color: selected
                          ? AppColors.primary
                          : AppColors.navBarUnselected,
                      size: 24,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 3),
            AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 200),
              style: TextStyle(
                fontSize: 11,
                fontWeight:
                    selected ? FontWeight.w700 : FontWeight.w400,
                color: selected
                    ? AppColors.primary
                    : AppColors.navBarUnselected,
              ),
              child: Text(widget.item.label),
            ),
          ],
        ),
      ),
    );
  }
}
