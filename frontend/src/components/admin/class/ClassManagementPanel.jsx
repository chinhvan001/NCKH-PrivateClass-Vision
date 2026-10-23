import { useEffect, useMemo, useState } from "react";

import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";
import CustomScrollbar from "../../common/CustomScrollbar";

const API_URL = "http://127.0.0.1:5000";

const CLASSES_API = `${API_URL}/api/admin/classes`;
const TEACHERS_API = `${API_URL}/api/admin/users`;

const emptyForm = {
  class_name: "",
  teacher_id: "",
  school_year: "2026-2027",
  row_count: 2,
  column_count: 2,
  status: "active",
};

const getErrorMessage = (error) => {
  const message = error?.message || "Có lỗi xảy ra. Vui lòng thử lại.";
  if (message === "Unauthorized.") {
    return "Phiên đăng nhập đã hết hạn.";
  }
  return message;
};

const getTeacherId = (teacher) => teacher?.uid || teacher?.id || "";

const getTeacherNameFromObject = (teacher) =>
  teacher?.full_name ||
  teacher?.display_name ||
  teacher?.name ||
  teacher?.email ||
  "Chưa có giáo viên";

const getClassCapacity = (classItem) => {
  const rows = Number(classItem?.row_count);
  const columns = Number(classItem?.column_count);

  if (
    !Number.isInteger(rows) ||
    rows <= 0 ||
    !Number.isInteger(columns) ||
    columns <= 0
  ) {
    return Number(classItem?.seat_capacity) > 0
      ? Number(classItem.seat_capacity)
      : 0;
  }
  return rows * columns;
};

const getClassSize = (classItem, seats = []) => {
  const capacity = getClassCapacity(classItem);
  if (capacity <= 0) return 0;

  if (Array.isArray(seats) && seats.length > 0) {
    const occupiedCount = seats.filter(
      (seat) => Boolean(seat?.student_id) || seat?.status === "occupied",
    ).length;
    return Math.min(capacity, occupiedCount);
  }

  const occupiedSeatCount = Number(classItem?.occupied_seat_count);
  if (Number.isFinite(occupiedSeatCount)) {
    return Math.max(0, Math.min(capacity, occupiedSeatCount));
  }

  const emptySeatCount = Number(classItem?.empty_seat_count);
  if (Number.isFinite(emptySeatCount)) {
    return Math.max(0, capacity - Math.max(0, emptySeatCount));
  }

  return 0;
};

const getRowCount = (classItem) => {
  const rows = Number(classItem?.row_count);
  return Number.isInteger(rows) && rows > 0 ? rows : 2;
};

const getColumnCount = (classItem) => {
  const columns = Number(classItem?.column_count);
  return Number.isInteger(columns) && columns > 0 ? columns : 2;
};

const buildSeatGrid = (classItem, seats = [], students = []) => {
  const rows = getRowCount(classItem);
  const columns = getColumnCount(classItem);
  const seatMap = new Map();

  const studentMap = new Map(
    students.map((s) => [s.student_id || s.id, s.full_name]),
  );

  seats.forEach((seat) => {
    const row = Number(seat?.row);
    const column = Number(seat?.column);

    if (
      Number.isInteger(row) &&
      Number.isInteger(column) &&
      row > 0 &&
      column > 0
    ) {
      seatMap.set(`${row}-${column}`, seat);
    }
  });

  const grid = [];

  for (let row = 1; row <= rows; row += 1) {
    for (let column = 1; column <= columns; column += 1) {
      const existingSeat = seatMap.get(`${row}-${column}`);
      const seatNumber = (row - 1) * columns + column;

      const seatId =
        existingSeat?.seat_id && existingSeat.seat_id.trim() !== ""
          ? existingSeat.seat_id
          : `S${String(seatNumber).padStart(2, "0")}`;

      const studentId = existingSeat?.student_id || null;
      const studentName =
        existingSeat?.student_name || studentMap.get(studentId) || "";

      grid.push({
        row,
        column,
        seat_id: seatId,
        student_id: studentId,
        student_name: studentName,
        status: existingSeat?.status || (studentId ? "occupied" : "empty"),
      });
    }
  }

  return grid;
};

const ClassManagementPanel = () => {
  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [optionsError, setOptionsError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);

  const [showClassForm, setShowClassForm] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const [confirmDeleteClass, setConfirmDeleteClass] = useState(null);

  const [selectedClass, setSelectedClass] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const [selectedSeatClass, setSelectedSeatClass] = useState(null);
  const [seatDetail, setSeatDetail] = useState(null);
  const [seatLoading, setSeatLoading] = useState(false);
  const [seatError, setSeatError] = useState("");

  const getToken = () => localStorage.getItem("idToken");

  const request = async (url, options = {}) => {
    const idToken = getToken();

    if (!idToken) {
      throw new Error("Unauthorized.");
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        Authorization: `Bearer ${idToken}`,
        ...(options.headers || {}),
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Không thể kết nối máy chủ.");
    }

    return data;
  };

  const loadClasses = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await request(CLASSES_API);
      setClasses(Array.isArray(data.data) ? data.data : []);
    } catch (loadError) {
      console.error("Load classes error:", loadError);
      setError(getErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  };

  const loadTeachers = async () => {
    try {
      setOptionsError("");
      const data = await request(TEACHERS_API);
      const list = Array.isArray(data.users)
        ? data.users
        : Array.isArray(data.teachers)
          ? data.teachers
          : [];
      setTeachers(list.filter((teacher) => teacher.is_active !== false));
    } catch (loadError) {
      console.error("Load teachers error:", loadError);
      setOptionsError(getErrorMessage(loadError));
    }
  };

  useEffect(() => {
    loadClasses();
    loadTeachers();
  }, []);

  const getTeacherName = (teacherId, classItem = null) => {
    if (classItem?.teacher_name) {
      return classItem.teacher_name;
    }
    const teacher = teachers.find((item) => getTeacherId(item) === teacherId);
    return getTeacherNameFromObject(teacher);
  };

  const filteredClasses = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return classes.filter((classItem) => {
      const teacher = teachers.find(
        (item) => getTeacherId(item) === classItem.teacher_id,
      );
      const teacherName =
        classItem.teacher_name || getTeacherNameFromObject(teacher);

      const matchesSearch =
        !keyword ||
        [
          classItem.class_name,
          classItem.teacher_id,
          teacherName,
          teacher?.email,
          classItem.school_year,
        ].some((value) =>
          String(value || "")
            .toLowerCase()
            .includes(keyword),
        );

      const matchesStatus =
        statusFilter === "all" || classItem.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [classes, search, statusFilter, teachers]);

  const classesPerPage = 10;
  const totalPages = Math.ceil(filteredClasses.length / classesPerPage);
  const safePage = totalPages ? Math.min(currentPage, totalPages) : 1;
  const currentClasses = filteredClasses.slice(
    (safePage - 1) * classesPerPage,
    safePage * classesPerPage,
  );

  const resetForm = () => {
    setFormData({ ...emptyForm });
    setFormError("");
  };

  const openAddClass = () => {
    setEditingClass(null);
    resetForm();
    setShowClassForm(true);
  };

  const openEditClass = (classItem) => {
    setEditingClass(classItem);
    setFormData({
      class_name: classItem.class_name || "",
      teacher_id: classItem.teacher_id || "",
      school_year: classItem.school_year || "",
      row_count: Number(classItem.row_count) > 0 ? Number(classItem.row_count) : 2,
      column_count: Number(classItem.column_count) > 0 ? Number(classItem.column_count) : 2,
      status: classItem.status || "active",
    });
    setFormError("");
    setShowClassForm(true);
  };

  const submitClass = async () => {
    const rowCount = Number(formData.row_count);
    const columnCount = Number(formData.column_count);

    if (
      !formData.class_name.trim() ||
      !formData.teacher_id ||
      !formData.school_year.trim()
    ) {
      setFormError("Vui lòng nhập đầy đủ thông tin lớp học.");
      return;
    }

    if (
      !Number.isInteger(rowCount) ||
      rowCount <= 0 ||
      !Number.isInteger(columnCount) ||
      columnCount <= 0
    ) {
      setFormError("Số hàng và số cột phải là số nguyên dương.");
      return;
    }

    try {
      setFormLoading(true);
      setFormError("");

      const url = editingClass
        ? `${CLASSES_API}/${editingClass.id}`
        : CLASSES_API;

      const data = await request(url, {
        method: editingClass ? "PUT" : "POST",
        body: JSON.stringify({
          class_name: formData.class_name.trim(),
          teacher_id: formData.teacher_id,
          school_year: formData.school_year.trim(),
          row_count: rowCount,
          column_count: columnCount,
          ...(editingClass ? { status: formData.status } : {}),
        }),
      });

      setClasses((current) =>
        editingClass
          ? current.map((item) =>
              item.id === editingClass.id ? data.data : item,
            )
          : [...current, data.data],
      );

      setShowClassForm(false);
      setEditingClass(null);
      resetForm();
    } catch (submitError) {
      console.error("Save class error:", submitError);
      setFormError(getErrorMessage(submitError));
    } finally {
      setFormLoading(false);
    }
  };

  const deleteClass = async () => {
    if (!confirmDeleteClass) return;
    try {
      await request(`${CLASSES_API}/${confirmDeleteClass.id}`, {
        method: "DELETE",
      });

      setClasses((current) =>
        current.filter((item) => item.id !== confirmDeleteClass.id),
      );

      if (selectedClass?.id === confirmDeleteClass.id) {
        setSelectedClass(null);
        setDetail(null);
      }

      if (selectedSeatClass?.id === confirmDeleteClass.id) {
        setSelectedSeatClass(null);
        setSeatDetail(null);
      }
    } catch (deleteError) {
      setError(getErrorMessage(deleteError));
    } finally {
      setConfirmDeleteClass(null);
    }
  };

  const loadDetail = async (classItem) => {
    try {
      setSelectedClass(classItem);
      setDetail(null);
      setDetailError("");
      setDetailLoading(true);

      const [classData, studentsData] = await Promise.all([
        request(`${CLASSES_API}/${classItem.id}`),
        request(`${CLASSES_API}/${classItem.id}/students`),
      ]);

      const currentClass = classData.data || classItem;
      const students = Array.isArray(studentsData.data)
        ? studentsData.data
        : [];

      setSelectedClass(currentClass);
      setDetail({ classInfo: currentClass, students });
    } catch (detailLoadError) {
      console.error("Load class detail error:", detailLoadError);
      setDetailError(getErrorMessage(detailLoadError));
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedClass(null);
    setDetail(null);
    setDetailError("");
  };

  const loadSeatMap = async (classItem) => {
    try {
      setSelectedSeatClass(classItem);
      setSeatDetail(null);
      setSeatError("");
      setSeatLoading(true);

      const [classData, studentsData, seatsData] = await Promise.all([
        request(`${CLASSES_API}/${classItem.id}`),
        request(`${CLASSES_API}/${classItem.id}/students`),
        request(`${CLASSES_API}/${classItem.id}/seats`),
      ]);

      const currentClass = classData.data || classItem;
      const students = Array.isArray(studentsData.data)
        ? studentsData.data
        : [];
      const seats = Array.isArray(seatsData.data) ? seatsData.data : [];
      const grid = buildSeatGrid(currentClass, seats, students);
      const occupiedSeatCount = grid.filter((seat) =>
        seat.student_name && seat.student_name.trim() !== ""
      ).length;
      const capacity = getClassCapacity(currentClass);
      const emptySeatCount = Math.max(0, capacity - occupiedSeatCount);

      setSelectedSeatClass(currentClass);
      setSeatDetail({
        classInfo: currentClass,
        students,
        seats,
        grid,
        capacity,
        occupiedSeatCount,
        emptySeatCount,
      });
    } catch (seatLoadError) {
      console.error("Load seat map error:", seatLoadError);
      setSeatError(getErrorMessage(seatLoadError));
    } finally {
      setSeatLoading(false);
    }
  };

  const closeSeatMap = () => {
    setSelectedSeatClass(null);
    setSeatDetail(null);
    setSeatError("");
  };

  const detailClass = detail?.classInfo || selectedClass;
  const detailRows = getRowCount(detailClass);
  const detailColumns = getColumnCount(detailClass);

  const seatClass = seatDetail?.classInfo || selectedSeatClass;
  const seatRows = getRowCount(seatClass);
  const seatColumns = getColumnCount(seatClass);

  return (
    <div className="class-management-page">
      <section className="class-stats-section">
        <h2>Quản lý lớp học</h2>

        <div className="class-stats-grid">
          <article className="class-stat-card blue">
            <div className="class-stat-icon">
              <Icon name="school" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Tổng số lớp</span>
              <strong>{loading ? "—" : classes.length}</strong>
              <small>Lớp học</small>
            </div>
          </article>

          <article className="class-stat-card green">
            <div className="class-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Đang hoạt động</span>
              <strong>
                {loading
                  ? "—"
                  : classes.filter((item) => item.status === "active").length}
              </strong>
              <small>Lớp học</small>
            </div>
          </article>

          <article className="class-stat-card orange">
            <div className="class-stat-icon">
              <Icon name="book" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Tổng sĩ số</span>
              <strong>
                {loading
                  ? "—"
                  : classes.reduce(
                      (total, item) => total + getClassSize(item),
                      0,
                    )}
              </strong>
              <small>Học sinh đang được xếp chỗ</small>
            </div>
          </article>

          <article className="class-stat-card healthy">
            <div className="class-stat-icon">
              <Icon name="users" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Đang hiển thị</span>
              <strong>{loading ? "—" : filteredClasses.length}</strong>
              <small>Kết quả lọc</small>
            </div>
          </article>
        </div>
      </section>

      <section className="class-panel">
        <div className="class-panel-heading">
          <div>
            <h2>Danh sách lớp học</h2>
            <p>Dữ liệu được tải từ hệ thống quản lý lớp học.</p>
          </div>

          <button
            type="button"
            className="add-account-button"
            onClick={openAddClass}
          >
            <Icon name="plus" size={17} />
            <span>Thêm lớp học</span>
          </button>
        </div>

        <div className="class-filters">
          <div className="class-search">
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Tìm theo tên lớp, giáo viên..."
            />
            <span className="class-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          <select
            className="class-status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Đang hoạt động</option>
            <option value="inactive">Ngừng hoạt động</option>
          </select>

          <button
            type="button"
            className="refresh-button"
            onClick={loadClasses}
          >
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        {error && <div className="class-error">{error}</div>}

        <div className="class-table-wrap">
          <table className="class-table">
            <thead>
              <tr>
                <th>Tên lớp</th>
                <th>Sĩ số</th>
                <th>Giáo viên</th>
                <th>Năm học</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="table-empty">
                    Đang tải danh sách lớp học...
                  </td>
                </tr>
              ) : currentClasses.length === 0 ? (
                <tr>
                  <td colSpan="6" className="table-empty">
                    Không có lớp học phù hợp.
                  </td>
                </tr>
              ) : (
                currentClasses.map((classItem) => (
                  <tr key={classItem.id}>
                    <td>
                      <div className="class-cell">
                        <div className="table-avatar">
                          <Icon name="school" size={18} />
                        </div>
                        <strong>{classItem.class_name}</strong>
                      </div>
                    </td>
                    <td>
                      <strong>{getClassSize(classItem)}</strong>
                    </td>
                    <td>{getTeacherName(classItem.teacher_id, classItem)}</td>
                    <td>{classItem.school_year}</td>
                    <td>
                      <span
                        className={`class-status ${
                          classItem.status === "active" ? "active" : "inactive"
                        }`}
                      >
                        {classItem.status === "active"
                          ? "Đang hoạt động"
                          : "Ngừng hoạt động"}
                      </span>
                    </td>
                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="detail-button"
                          title="Xem chi tiết lớp"
                          onClick={() => loadDetail(classItem)}
                        >
                          <Icon name="eye" size={18} />
                        </button>

                        <button
                          type="button"
                          className="detail-button"
                          title="Xem sơ đồ lớp"
                          onClick={() => loadSeatMap(classItem)}
                        >
                          <Icon name="school" size={18} />
                        </button>

                        <button
                          type="button"
                          className="edit-button"
                          title="Chỉnh sửa"
                          onClick={() => openEditClass(classItem)}
                        >
                          <Icon name="edit" size={18} />
                        </button>

                        <button
                          type="button"
                          className="delete-button"
                          title="Vô hiệu hóa"
                          onClick={() => setConfirmDeleteClass(classItem)}
                        >
                          <Icon name="trash" size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="class-pagination">
          <span>
            {filteredClasses.length
              ? `${(safePage - 1) * classesPerPage + 1}-${Math.min(
                  safePage * classesPerPage,
                  filteredClasses.length,
                )}`
              : "0"}{" "}
            trên {filteredClasses.length} lớp
          </span>

          <div>
            <button
              type="button"
              disabled={safePage === 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
            >
              <Icon name="arrowLeft" size={15} />
            </button>

            <button
              type="button"
              disabled={safePage === totalPages || totalPages === 0}
              onClick={() =>
                setCurrentPage((page) => Math.min(totalPages, page + 1))
              }
            >
              <Icon name="arrowRight" size={15} />
            </button>
          </div>
        </div>
      </section>

      {showClassForm && (
        <div
          className="class-modal-overlay"
          onClick={() => !formLoading && setShowClassForm(false)}
        >
          <div className="class-modal" onClick={(e) => e.stopPropagation()}>
            <div className="class-modal-header">
              <div>
                <h2>{editingClass ? "Chỉnh sửa lớp học" : "Thêm lớp học"}</h2>
              </div>
              <button
                type="button"
                className="edit-teacher-close"
                onClick={() => setShowClassForm(false)}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-modal-content">
              <label>
                <span>Tên lớp</span>
                <input
                  value={formData.class_name}
                  onChange={(e) =>
                    setFormData({ ...formData, class_name: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Giáo viên chủ nhiệm</span>
                <select
                  value={formData.teacher_id}
                  onChange={(e) =>
                    setFormData({ ...formData, teacher_id: e.target.value })
                  }
                  disabled={formLoading}
                >
                  <option value="">Chọn giáo viên</option>
                  {teachers.map((teacher) => (
                    <option
                      key={getTeacherId(teacher)}
                      value={getTeacherId(teacher)}
                    >
                      {getTeacherNameFromObject(teacher)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Năm học</span>
                <input
                  value={formData.school_year}
                  placeholder="2026-2027"
                  onChange={(e) =>
                    setFormData({ ...formData, school_year: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Số hàng</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={formData.row_count}
                  onChange={(e) =>
                    setFormData({ ...formData, row_count: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Số cột</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={formData.column_count}
                  onChange={(e) =>
                    setFormData({ ...formData, column_count: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <div
                style={{
                  padding: "12px 14px",
                  background: "#f8fafc",
                  borderRadius: "10px",
                  color: "#475569",
                  fontSize: "14px",
                }}
              >
                Sức chứa:{" "}
                <strong>
                  {Number(formData.row_count) > 0 &&
                  Number(formData.column_count) > 0
                    ? Number(formData.row_count) * Number(formData.column_count)
                    : 0}{" "}
                  chỗ
                </strong>
              </div>

              {editingClass && (
                <label>
                  <span>Trạng thái</span>
                  <select
                    value={formData.status}
                    onChange={(e) =>
                      setFormData({ ...formData, status: e.target.value })
                    }
                    disabled={formLoading}
                  >
                    <option value="active">Đang hoạt động</option>
                    <option value="inactive">Ngừng hoạt động</option>
                  </select>
                </label>
              )}

              {optionsError && (
                <div className="class-form-error">{optionsError}</div>
              )}
              {formError && <div className="class-form-error">{formError}</div>}
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={() => setShowClassForm(false)}
                disabled={formLoading}
              >
                Hủy
              </button>
              <button
                type="button"
                className="add-account-button"
                onClick={submitClass}
                disabled={formLoading}
              >
                {formLoading ? "Đang lưu..." : "Lưu lớp"}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedClass && (
        <div className="class-modal-overlay" onClick={closeDetail}>
          <div
            className="class-modal class-detail-wide"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="class-detail-header">
              <div>
                <h2>{detailClass?.class_name || "Chi tiết lớp học"}</h2>
                <p>
                  Thông tin chi tiết lớp học và danh sách học sinh hiện tại.
                </p>
              </div>
            </div>

            {detailLoading ? (
              <div className="class-detail-state">
                Đang tải thông tin lớp học...
              </div>
            ) : detailError ? (
              <div className="class-matrix-error">{detailError}</div>
            ) : (
              <div className="class-modal-content">
                <div className="class-detail-info-section">
                  <div className="class-detail-section-header">
                    <h3>Thông tin chung</h3>
                    <p>
                      Các thông tin cơ bản về môn học, giáo viên và sức chứa.
                    </p>
                  </div>

                  <div className="class-detail-info-grid">
                    <div className="class-detail-info-item">
                      <span>Giáo viên:</span>
                      <strong>
                        {getTeacherName(detailClass?.teacher_id, detailClass)}
                      </strong>
                    </div>
                    <div className="class-detail-info-item">
                      <span>Năm học:</span>
                      <strong>{detailClass?.school_year || "—"}</strong>
                    </div>
                    <div className="class-detail-info-item">
                      <span>Kích thước:</span>
                      <strong>
                        {detailRows} hàng × {detailColumns} cột
                      </strong>
                    </div>
                    <div className="class-detail-info-item">
                      <span>Sức chứa:</span>
                      <strong>{getClassCapacity(detailClass)} chỗ</strong>
                    </div>
                    <div className="class-detail-info-item">
                      <span>Sĩ số:</span>
                      <strong>{getClassSize(detailClass)} học sinh</strong>
                    </div>
                    <div className="class-detail-info-item">
                      <span>Trạng thái:</span>
                      <span
                        className={`class-status ${
                          detailClass?.status === "active"
                            ? "active"
                            : "inactive"
                        }`}
                      >
                        {detailClass?.status === "active"
                          ? "Đang hoạt động"
                          : "Ngừng hoạt động"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="class-detail-workspace" style={{ gridTemplateColumns: "1fr" }}>
                  <section>
                    <div className="class-detail-section-header">
                      <h3>
                        Danh sách học sinh ({detail?.students?.length || 0})
                      </h3>
                    </div>

                    {detail?.students?.length === 0 ? (
                      <p className="class-no-data">Chưa có học sinh nào trong lớp này.</p>
                    ) : (
                      <CustomScrollbar height="auto" className="class-modal-content overflow-x-auto" style={{ padding: 0, marginTop: "16px" }}>
                        <div className="student-table-wrap min-w-[900px]">
                          <table className="student-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                              <tr>
                                <th className="col-stt">STT</th>
                                <th className="col-fullname">HỌ VÀ TÊN</th>
                                <th className="col-gender">GIỚI TÍNH</th>
                                <th className="col-birthday">SINH NHẬT</th>
                                <th className="col-phone">SĐT PHỤ HUYNH</th>
                                <th className="col-note">GHI CHÚ</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail?.students
                                ?.slice()
                                ?.sort((a, b) => {
                                  const getFirstName = (name) => {
                                    const parts = (name || "").trim().split(" ");
                                    return parts[parts.length - 1];
                                  };
                                  const firstNameA = getFirstName(a.full_name);
                                  const firstNameB = getFirstName(b.full_name);
                                  
                                  const compareFirstName = firstNameA.localeCompare(firstNameB, "vi", { sensitivity: "base" });
                                  if (compareFirstName !== 0) return compareFirstName;
                                  
                                  return (a.full_name || "").localeCompare(b.full_name || "", "vi", { sensitivity: "base" });
                                })
                                ?.map((student, index) => {
                                  let formattedBirthday = "—";
                                  if (student.birthday) {
                                    const date = new Date(student.birthday);
                                    if (!isNaN(date.getTime())) {
                                      formattedBirthday = date.toLocaleDateString("vi-VN");
                                    } else {
                                      formattedBirthday = student.birthday;
                                    }
                                  }

                                  return (
                                    <tr key={student.student_id || index} style={{ borderBottom: "1px solid #edf2f7" }}>
                                      <td className="col-stt" style={{ padding: "12px 14px", color: "#64748b", fontWeight: "500" }}>{index + 1}</td>
                                      <td className="col-fullname" style={{ padding: "12px 14px", fontWeight: "600", color: "#1e293b" }}>{student.full_name}</td>
                                      <td className="col-gender" style={{ padding: "12px 14px", color: "#64748b" }}>{student.gender || "—"}</td>
                                      <td className="col-birthday" style={{ padding: "12px 14px", color: "#64748b" }}>{formattedBirthday}</td>
                                      <td className="col-phone" style={{ padding: "12px 14px", color: "#64748b" }}>{student.parent_phone || "—"}</td>
                                      <td className="col-note" style={{ padding: "12px 14px", color: "#64748b" }}>{student.note || "—"}</td>
                                    </tr>
                                  );
                                })}
                            </tbody>
                          </table>
                        </div>
                      </CustomScrollbar>
                    )}
                  </section>
                </div>
              </div>
            )}

            <div className="class-modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={closeDetail}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedSeatClass && (
        <div className="class-modal-overlay" onClick={closeSeatMap}>
          <div
            className="class-modal class-matrix-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>Sơ đồ chỗ ngồi — {seatClass?.class_name}</h2>
                <p>
                  Sơ đồ bố trí {seatRows} hàng x {seatColumns} cột trong phòng
                  học.
                </p>
              </div>
              <button
                type="button"
                className="edit-teacher-close"
                onClick={closeSeatMap}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            {seatLoading ? (
              <div className="class-matrix-loading">
                Đang tải sơ đồ chỗ ngồi...
              </div>
            ) : seatError ? (
              <div className="class-matrix-error">{seatError}</div>
            ) : (
              <div className="class-modal-content">
                <div className="class-matrix-summary">
                  <div className="class-matrix-summary-card">
                    <span>Sức chứa phòng</span>
                    <strong>{seatDetail?.capacity || 0} chỗ</strong>
                  </div>
                  <div className="class-matrix-summary-card">
                    <span>Đã xếp chỗ</span>
                    <strong style={{ color: "#2563eb" }}>
                      {seatDetail?.occupiedSeatCount || 0} học sinh
                    </strong>
                  </div>
                  <div className="class-matrix-summary-card">
                    <span>Ghế còn trống</span>
                    <strong style={{ color: "#16a34a" }}>
                      {seatDetail?.emptySeatCount || 0} chỗ
                    </strong>
                  </div>
                </div>

                <div className="class-matrix-section">
                  <div className="class-matrix-section-header">
                    <h3>Bản đồ chỗ ngồi</h3>
                    <p>Hiển thị chi tiết vị trí từng ghế ngồi.</p>
                  </div>

                  <div className="class-matrix-preview">
                    <div
                      className="class-seat-grid"
                      style={{
                        gridTemplateColumns: `repeat(${seatColumns}, minmax(0, 1fr))`,
                      }}
                    >
                      {seatDetail?.grid?.map((seat, index) => {
                        const isOccupied = Boolean(seat.student_name && seat.student_name.trim() !== "");
                        
                        return (
                          <div 
                            key={index} 
                            className={`test-seat-card ${isOccupied ? 'occupied' : 'empty'}`}
                          >
                            <div className="seat-code" style={{ fontWeight: 'bold' }}>
                              {seat?.seat_id ? seat.seat_id.replace(/^S/i, '') : index + 1}
                            </div>

                            {isOccupied && seat.student_name && (
                              <div className="seat-info" style={{ marginTop: '4px' }}>
                                {seat.student_name}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="class-modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={closeSeatMap}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDeleteClass && (
        <ConfirmModal
          title="Vô hiệu hóa lớp học"
          message={`Bạn có chắc chắn muốn vô hiệu hóa lớp "${confirmDeleteClass.class_name}"? Lớp học sẽ chuyển sang trạng thái Ngừng hoạt động.`}
          onConfirm={deleteClass}
          onCancel={() => setConfirmDeleteClass(null)}
        />
      )}
    </div>
  );
};

export default ClassManagementPanel;