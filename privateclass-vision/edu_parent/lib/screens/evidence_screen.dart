import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';

class EvidenceScreen extends StatefulWidget {
  const EvidenceScreen({super.key});

  @override
  State<EvidenceScreen> createState() => _EvidenceScreenState();
}

class _EvidenceScreenState extends State<EvidenceScreen> {
  String _activeTab = 'Tất cả';
  final List<String> _tabs = ['Tất cả', 'Hình ảnh', 'Video', 'Ghi chú'];

  final List<Map<String, dynamic>> _items = [
    {'type': 'image', 'date': '16/05/2024 - 08:45', 'color': AppColors.accentLight},
    {'type': 'image', 'date': '15/05/2024 - 10:20', 'color': const Color(0xFFE8F5E9)},
    {'type': 'image', 'date': '14/05/2024 - 08:15', 'color': AppColors.orangeLight},
    {'type': 'image', 'date': '10/05/2024 - 10:05', 'color': AppColors.accentLight},
    {'type': 'image', 'date': '13/05/2024 - 09:30', 'color': const Color(0xFFE8F5E9)},
    {'type': 'image', 'date': '12/05/2024 - 11:00', 'color': AppColors.orangeLight},
  ];

  List<Map<String, dynamic>> get _filtered {
    if (_activeTab == 'Tất cả') return _items;
    if (_activeTab == 'Hình ảnh') {
      return _items.where((i) => i['type'] == 'image').toList();
    }
    if (_activeTab == 'Video') {
      return _items.where((i) => i['type'] == 'video').toList();
    }
    return _items.where((i) => i['type'] == 'note').toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Minh chứng thiếu tập trung', style: AppTextStyles.heading2),
      ),
      body: Column(
        children: [
          // Tabs
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _tabs.map((t) {
                  final selected = t == _activeTab;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _activeTab = t),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
                        decoration: BoxDecoration(
                          color: selected ? AppColors.primary : Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: selected ? AppColors.primary : AppColors.divider,
                          ),
                        ),
                        child: Text(
                          t,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: selected ? Colors.white : AppColors.textSecondary,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          // Grid
          Expanded(
            child: _filtered.isEmpty
                ? const Center(
                    child: Text('Không có dữ liệu', style: AppTextStyles.body2),
                  )
                : GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1,
                    ),
                    itemCount: _filtered.length,
                    itemBuilder: (context, index) {
                      final item = _filtered[index];
                      return Container(
                        decoration: BoxDecoration(
                          color: item['color'] as Color,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              item['type'] == 'image' ? Icons.image : Icons.videocam,
                              color: AppColors.primary,
                              size: 48,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              item['date'] as String,
                              style: AppTextStyles.small,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
