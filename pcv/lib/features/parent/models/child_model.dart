import 'package:cloud_firestore/cloud_firestore.dart';

class ChildModel {
  final String id;
  final String parentId;
  final String name;
  final String className;
  final String schoolName;
  final int avgFocusPercent;

  const ChildModel({
    required this.id,
    required this.parentId,
    required this.name,
    required this.className,
    required this.schoolName,
    required this.avgFocusPercent,
  });

  factory ChildModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return ChildModel(
      id: doc.id,
      parentId: d['parentId'] as String? ?? '',
      name: d['name'] as String? ?? '',
      className: d['className'] as String? ?? '',
      schoolName: d['schoolName'] as String? ?? '',
      avgFocusPercent: (d['avgFocusPercent'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toMap() => {
        'parentId': parentId,
        'name': name,
        'className': className,
        'schoolName': schoolName,
        'avgFocusPercent': avgFocusPercent,
      };
}
