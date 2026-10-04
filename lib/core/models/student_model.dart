class StudentModel {
  final String id;
  final String name;
  final String short;
 
  final int? row;
  final int? column;
 
  const StudentModel({
    required this.id,
    required this.name,
    required this.short,
    this.row,
    this.column,
  });
}
 