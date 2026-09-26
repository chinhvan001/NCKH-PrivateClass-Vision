class StudentModel {
  final String id;
  final String name;
  final String short;

  const StudentModel({
    required this.id,
    required this.name,
    required this.short, required int row, required int column,
  });

  get row => null;

  get column => null;
}
