import { useEffect, useMemo, useState } from "react";
import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";

const API_URL = "http://127.0.0.1:5000";

const TEACHERS_API = `${API_URL}/api/admin/users`;
const CLASSROOMS_API = `${API_URL}/api/admin/classrooms`;
const CLASSES_API = `${API_URL}/api/admin/classes`;

const ClassManagementPanel = () => {
  const CLASSES_PER_PAGE = 10;

  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [classrooms, setClassrooms] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadingOptions, setLoadingOptions] = useState(true);

  const [error, setError] = useState("");
  const [optionsError, setOptionsError] = useState("");

  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const [showAddClass, setShowAddClass] = useState(false);
  const [selectedClass, setSelectedClass] = useState(null);
  const [selectedHealth, setSelectedHealth] = useState(null);
  const [editingClass, setEditingClass] = useState(null);

  const [selectedMatrixClass, setSelectedMatrixClass] = useState(null);
  const [matrixData, setMatrixData] = useState(null);
  const [matrixLoading, setMatrixLoading] = useState(false);
  const [matrixError, setMatrixError] = useState("");
  const [matrixSaving, setMatrixSaving] = useState(false);

  const [confirmDeleteClass, setConfirmDeleteClass] = useState(null);

  const [formData, setFormData] = useState({
    class_name: "",
    teacher_id: "",
    classroom_id: "",
    row_number: 1,
    column_number: 1,
    is_active: true,
  });

  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const getToken = () => {
    return localStorage.getItem("idToken");
  };

  const getAuthHeaders = () => {
    const idToken = getToken();

    return {
      Authorization: `Bearer ${idToken}`,
    };
  };

  const fetchClasses = async () => {
    try {
      setLoading(true);
      setError("");

      const idToken = getToken();

      if (!idToken) {
        setError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const response = await fetch(CLASSES_API, {
        method: "GET",
        headers: getAuthHeaders(),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Không thể lấy danh sách lớp học.");
      }

      setClasses(Array.isArray(data.classes) ? data.classes : []);
    } catch (error) {
      console.error("Fetch classes error:", error);
      setError(error.message || "Không thể lấy danh sách lớp học.");
    } finally {
      setLoading(false);
    }
  };

  const fetchFormOptions = async () => {
    try {
      setLoadingOptions(true);
      setOptionsError("");

      const idToken = getToken();

      if (!idToken) {
        setOptionsError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const headers = getAuthHeaders();

      const [teachersResponse, classroomsResponse] = await Promise.all([
        fetch(TEACHERS_API, {
          method: "GET",
          headers,
        }),
        fetch(CLASSROOMS_API, {
          method: "GET",
          headers,
        }),
      ]);

      const teachersData = await teachersResponse.json();
      const classroomsData = await classroomsResponse.json();

      if (!teachersResponse.ok || !teachersData.success) {
        throw new Error(
          teachersData.message || "Không thể lấy danh sách giáo viên.",
        );
      }

      if (!classroomsResponse.ok || !classroomsData.success) {
        throw new Error(
          classroomsData.message || "Không thể lấy danh sách phòng học.",
        );
      }

      const teacherList = Array.isArray(teachersData.users)
        ? teachersData.users
        : Array.isArray(teachersData.teachers)
          ? teachersData.teachers
          : [];

      setTeachers(teacherList.filter((teacher) => teacher.is_active !== false));

      const classroomList = Array.isArray(classroomsData.classrooms)
        ? classroomsData.classrooms
        : Array.isArray(classroomsData.rooms)
          ? classroomsData.rooms
          : [];

      setClassrooms(
        classroomList.filter((classroom) => classroom.is_active !== false),
      );
    } catch (error) {
      console.error("Fetch class options error:", error);

      setOptionsError(
        error.message || "Không thể lấy dữ liệu giáo viên và phòng học.",
      );
    } finally {
      setLoadingOptions(false);
    }
  };

  useEffect(() => {
    fetchClasses();
    fetchFormOptions();
  }, []);

  const filteredClasses = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return classes.filter((classItem) => {
      const className = String(classItem.class_name || "").toLowerCase();

      const classId = String(classItem.id || "").toLowerCase();

      const teacherName = String(classItem.teacher_name || "").toLowerCase();

      const classroomName = String(
        classItem.classroom_name || "",
      ).toLowerCase();

      return (
        !keyword ||
        className.includes(keyword) ||
        classId.includes(keyword) ||
        teacherName.includes(keyword) ||
        classroomName.includes(keyword)
      );
    });
  }, [classes, search]);

  const getAverageEngagement = (classItem) => {
    const value =
      classItem.average_engagement ??
      classItem.avg_engagement ??
      classItem.engagement_average ??
      null;

    if (value === null || value === undefined || value === "") {
      return null;
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return null;
    }

    return number;
  };

  const healthyClasses = classes.filter((classItem) => {
    const engagement = getAverageEngagement(classItem);

    return (
      classItem.is_active !== false && engagement !== null && engagement >= 70
    );
  }).length;

  const attentionClasses = classes.filter((classItem) => {
    const engagement = getAverageEngagement(classItem);

    return (
      classItem.is_active !== false && engagement !== null && engagement < 70
    );
  }).length;

  const totalClasses = classes.length;

  const managedClasses = classes.filter(
    (classItem) => classItem.is_active !== false,
  ).length;

  const totalPages = Math.ceil(filteredClasses.length / CLASSES_PER_PAGE);

  const safeCurrentPage =
    totalPages === 0 ? 1 : Math.min(currentPage, totalPages);

  const startIndex = (safeCurrentPage - 1) * CLASSES_PER_PAGE;

  const currentClasses = filteredClasses.slice(
    startIndex,
    startIndex + CLASSES_PER_PAGE,
  );

  const displayStart = filteredClasses.length === 0 ? 0 : startIndex + 1;

  const displayEnd = Math.min(
    startIndex + CLASSES_PER_PAGE,
    filteredClasses.length,
  );

  const handleSearch = (value) => {
    setSearch(value);
    setCurrentPage(1);
  };

  const getTeacherIdentifier = (teacher) => {
    return teacher.uid || teacher.id || "";
  };

  const getTeacherName = (teacherUid) => {
    if (!teacherUid) {
      return "";
    }

    const teacher = teachers.find(
      (item) => item.uid === teacherUid || item.id === teacherUid,
    );

    return teacher?.name || teacher?.email || "";
  };

  const getClassroomName = (classroomId) => {
    if (!classroomId) {
      return "";
    }

    const classroom = classrooms.find(
      (item) => item.id === classroomId || item.classroom_id === classroomId,
    );

    return (
      classroom?.classroom_name ||
      classroom?.class_name ||
      classroom?.room_name ||
      classroom?.name ||
      ""
    );
  };

  const getClassStudentCount = (classItem) => {
    const studentCount =
      classItem.student_count ??
      classItem.students_count ??
      classItem.number_of_students;

    if (
      studentCount !== undefined &&
      studentCount !== null &&
      studentCount !== ""
    ) {
      return studentCount;
    }

    const rows = Number(classItem.row_number || 0);
    const columns = Number(classItem.column_number || 0);

    if (rows > 0 && columns > 0) {
      return rows * columns;
    }

    return null;
  };

  const renderEngagement = (classItem) => {
    const engagement = getAverageEngagement(classItem);

    if (engagement === null) {
      return <span className="class-engagement empty">—</span>;
    }

    return (
      <span
        className={`class-engagement ${
          engagement >= 70 ? "good" : "attention"
        }`}
      >
        {engagement.toFixed(0)}%
      </span>
    );
  };

  const resetForm = () => {
    setFormData({
      class_name: "",
      teacher_id: "",
      classroom_id: "",
      row_number: 1,
      column_number: 1,
      is_active: true,
    });

    setFormError("");
  };

  const handleOpenAddClass = () => {
    resetForm();
    setEditingClass(null);
    setShowAddClass(true);

    if (teachers.length === 0 || classrooms.length === 0) {
      fetchFormOptions();
    }
  };

  const handleEditClass = (classItem) => {
    setEditingClass(classItem);

    setFormData({
      class_name: classItem.class_name || "",
      teacher_id: classItem.teacher_id || "",
      classroom_id: classItem.classroom_id || "",
      row_number: classItem.row_number || 1,
      column_number: classItem.column_number || 1,
      is_active: classItem.is_active !== false,
    });

    setFormError("");
    setShowAddClass(true);

    if (teachers.length === 0 || classrooms.length === 0) {
      fetchFormOptions();
    }
  };

  const handleCloseForm = () => {
    if (formLoading) {
      return;
    }

    setShowAddClass(false);
    setEditingClass(null);
    resetForm();
  };

  const handleFormChange = (field, value) => {
    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const handleSubmitClass = async () => {
    try {
      setFormLoading(true);
      setFormError("");

      const idToken = getToken();

      if (!idToken) {
        setFormError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const payload = {
        class_name: formData.class_name.trim(),
        teacher_id: formData.teacher_id || null,
        classroom_id: formData.classroom_id,
        row_number: Number(formData.row_number),
        column_number: Number(formData.column_number),
        is_active: formData.is_active,
      };

      if (!payload.class_name) {
        setFormError("Tên lớp không được để trống.");
        return;
      }

      if (!payload.classroom_id) {
        setFormError("Vui lòng chọn phòng học.");
        return;
      }

      if (!Number.isInteger(payload.row_number) || payload.row_number < 1) {
        setFormError("Số hàng phải lớn hơn hoặc bằng 1.");
        return;
      }

      if (
        !Number.isInteger(payload.column_number) ||
        payload.column_number < 1
      ) {
        setFormError("Số cột phải lớn hơn hoặc bằng 1.");
        return;
      }

      const url = editingClass
        ? `${CLASSES_API}/${editingClass.id}`
        : CLASSES_API;

      const method = editingClass ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Không thể lưu lớp học.");
      }

      await fetchClasses();

      setShowAddClass(false);
      setEditingClass(null);
      resetForm();
    } catch (error) {
      console.error("Save class error:", error);

      setFormError(error.message || "Không thể lưu lớp học.");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteClass = async (classItem) => {
    try {
      const idToken = getToken();

      if (!idToken) {
        setError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const response = await fetch(`${CLASSES_API}/${classItem.id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Không thể xóa lớp học.");
      }

      await fetchClasses();

      if (selectedClass && selectedClass.id === classItem.id) {
        setSelectedClass(null);
      }

      setConfirmDeleteClass(null);
    } catch (error) {
      console.error("Delete class error:", error);

      setError(error.message || "Không thể xóa lớp học.");

      setConfirmDeleteClass(null);
    }
  };

  const handleRefresh = () => {
    setSearch("");
    setCurrentPage(1);
    fetchClasses();
    fetchFormOptions();
  };

  const handleViewDetails = (classItem) => {
    setSelectedClass(classItem);
  };

  const handleOpenMatrix = async (classItem) => {
    try {
      setSelectedMatrixClass(classItem);
      setMatrixData(null);
      setMatrixError("");
      setMatrixLoading(true);

      const idToken = getToken();

      if (!idToken) {
        setMatrixError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const response = await fetch(`${CLASSES_API}/${classItem.id}/seats`, {
        method: "GET",
        headers: getAuthHeaders(),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Không thể lấy ma trận lớp học.");
      }

      setMatrixData(data);
    } catch (error) {
      console.error("Get class matrix error:", error);

      setMatrixError(error.message || "Không thể lấy ma trận lớp học.");
    } finally {
      setMatrixLoading(false);
    }
  };

  const handleCloseMatrix = () => {
    if (matrixSaving) {
      return;
    }

    setSelectedMatrixClass(null);
    setMatrixData(null);
    setMatrixError("");
  };

  const handleMatrixChange = (field, value) => {
    setMatrixData((current) => ({
      ...current,
      [field]: Math.max(1, Number(value) || 1),
    }));
  };

  const handleSaveMatrix = async () => {
    try {
      setMatrixSaving(true);
      setMatrixError("");

      const idToken = getToken();

      if (!idToken) {
        setMatrixError("Phiên đăng nhập đã hết hạn.");
        return;
      }

      const rowNumber = Number(matrixData?.row_number);

      const columnNumber = Number(matrixData?.column_number);

      if (!Number.isInteger(rowNumber) || rowNumber < 1) {
        setMatrixError("Số hàng phải lớn hơn hoặc bằng 1.");
        return;
      }

      if (!Number.isInteger(columnNumber) || columnNumber < 1) {
        setMatrixError("Số cột phải lớn hơn hoặc bằng 1.");
        return;
      }

      const response = await fetch(`${CLASSES_API}/${selectedMatrixClass.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({
          row_number: rowNumber,
          column_number: columnNumber,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Không thể cập nhật ma trận.");
      }

      await fetchClasses();

      setSelectedMatrixClass(null);
      setMatrixData(null);
      setMatrixError("");
    } catch (error) {
      console.error("Save class matrix error:", error);

      setMatrixError(error.message || "Không thể cập nhật ma trận.");
    } finally {
      setMatrixSaving(false);
    }
  };

  return (
    <>
      <section className="class-stats-section">
        <h2>Quản lý lớp học</h2>

        <div className="class-stats-grid">
          <article className="class-stat-card blue">
            <div className="class-stat-icon">
              <Icon name="school" size={21} />
            </div>

            <div className="class-stat-info">
              <span>Tổng số lớp</span>
              <strong>{loading ? "—" : totalClasses}</strong>
              <small>Lớp học</small>
            </div>
          </article>

          <button
            type="button"
            className="class-stat-card green clickable"
            onClick={() => setSelectedHealth("managed")}
          >
            <div className="class-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>

            <div className="class-stat-info">
              <span>Đang quản lý</span>
              <strong>{loading ? "—" : managedClasses}</strong>
              <small>Lớp học</small>
            </div>

            <div className="class-stat-arrow">
              <Icon name="arrowRight" size={18} />
            </div>
          </button>

          <button
            type="button"
            className="class-stat-card healthy clickable"
            onClick={() => setSelectedHealth("healthy")}
          >
            <div className="class-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>

            <div className="class-stat-info">
              <span>Lớp hoạt động tốt</span>
              <strong>{loading ? "—" : healthyClasses}</strong>
              <small>Mức tập trung ≥ 70%</small>
            </div>

            <div className="class-stat-arrow">
              <Icon name="arrowRight" size={18} />
            </div>
          </button>

          <button
            type="button"
            className="class-stat-card orange clickable"
            onClick={() => setSelectedHealth("attention")}
          >
            <div className="class-stat-icon">
              <Icon name="alertCircle" size={21} />
            </div>

            <div className="class-stat-info">
              <span>Lớp cần chú ý</span>
              <strong>{loading ? "—" : attentionClasses}</strong>
              <small>Mức tập trung &lt; 70%</small>
            </div>

            <div className="class-stat-arrow">
              <Icon name="arrowRight" size={18} />
            </div>
          </button>
        </div>
      </section>

      <section className="class-panel">
        <div className="class-panel-heading">
          <div>
            <h2>Danh sách lớp học</h2>
            <p>Quản lý danh sách các lớp học trong hệ thống.</p>
          </div>

          <button
            type="button"
            className="add-account-button"
            onClick={handleOpenAddClass}
          >
            <Icon name="plus" size={17} />
            <span>Thêm lớp học</span>
          </button>
        </div>

        <div className="class-filters">
          <div className="class-search">
            <input
              type="text"
              value={search}
              onChange={(event) => handleSearch(event.target.value)}
              placeholder="Tìm kiếm theo tên lớp..."
            />

            <span className="class-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          <button
            type="button"
            className="refresh-button"
            onClick={handleRefresh}
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
                <th>GVCN</th>
                <th>Phòng học</th>
                <th>Sĩ số</th>
                <th>Mức độ tập trung TB</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="table-empty">
                    Đang tải danh sách lớp học...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="7" className="table-empty">
                    Không thể tải danh sách lớp học.
                  </td>
                </tr>
              ) : filteredClasses.length === 0 ? (
                <tr>
                  <td colSpan="7" className="table-empty">
                    Không tìm thấy lớp học.
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

                        <div>{classItem.class_name}</div>
                      </div>
                    </td>

                    <td>
                      {classItem.teacher_name ||
                        getTeacherName(classItem.teacher_id) ||
                        "—"}
                    </td>

                    <td>
                      {classItem.classroom_name ||
                        getClassroomName(classItem.classroom_id) ||
                        "—"}
                    </td>

                    <td>{getClassStudentCount(classItem) ?? "—"}</td>

                    <td>{renderEngagement(classItem)}</td>

                    <td>
                      <span
                        className={
                          classItem.is_active !== false
                            ? "class-status active"
                            : "class-status inactive"
                        }
                      >
                        {classItem.is_active !== false
                          ? "Đang hoạt động"
                          : "Ngừng hoạt động"}
                      </span>
                    </td>

                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="edit-button"
                          title="Chỉnh sửa"
                          onClick={() => handleEditClass(classItem)}
                        >
                          <Icon name="edit" size={18} />
                        </button>

                        <button
                          type="button"
                          className="detail-button"
                          title="Xem chi tiết"
                          onClick={() => handleViewDetails(classItem)}
                        >
                          <Icon name="eye" size={18} />
                        </button>

                        <button
                          type="button"
                          className="detail-button"
                          title="Quản lý sĩ số"
                          onClick={() => handleOpenMatrix(classItem)}
                        >
                          <Icon name="grid" size={18} />
                        </button>

                        <button
                          type="button"
                          className="delete-button"
                          title="Xóa lớp"
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
            Hiển thị {displayStart}-{displayEnd} trên {filteredClasses.length}{" "}
            lớp
          </span>

          <div>
            <button
              type="button"
              disabled={safeCurrentPage === 1}
              onClick={() => setCurrentPage(1)}
            >
              <Icon name="first" size={15} />
            </button>

            <button
              type="button"
              disabled={safeCurrentPage === 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
            >
              <Icon name="arrowLeft" size={15} />
            </button>

            {Array.from(
              {
                length: totalPages,
              },
              (_, index) => index + 1,
            ).map((page) => (
              <button
                key={page}
                type="button"
                className={safeCurrentPage === page ? "current-page" : ""}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}

            <button
              type="button"
              disabled={safeCurrentPage === totalPages || totalPages === 0}
              onClick={() =>
                setCurrentPage((page) => Math.min(totalPages, page + 1))
              }
            >
              <Icon name="arrowRight" size={15} />
            </button>

            <button
              type="button"
              disabled={safeCurrentPage === totalPages || totalPages === 0}
              onClick={() => setCurrentPage(totalPages)}
            >
              <Icon name="last" size={15} />
            </button>
          </div>
        </div>
      </section>

      {showAddClass && (
        <div className="class-modal-overlay" onClick={handleCloseForm}>
          <div
            className="class-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>{editingClass ? "Chỉnh sửa lớp học" : "Thêm lớp học"}</h2>

                <p>
                  {editingClass
                    ? "Cập nhật thông tin lớp học."
                    : "Tạo lớp học mới trong hệ thống."}
                </p>
              </div>

              <button
                type="button"
                className="edit-teacher-close"
                onClick={handleCloseForm}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-modal-content">
              <label>
                <span>Tên lớp</span>

                <input
                  type="text"
                  value={formData.class_name}
                  onChange={(event) =>
                    handleFormChange("class_name", event.target.value)
                  }
                  placeholder="Ví dụ: 10A1"
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Giáo viên chủ nhiệm</span>

                <select
                  value={formData.teacher_id}
                  onChange={(event) =>
                    handleFormChange("teacher_id", event.target.value)
                  }
                  disabled={formLoading || loadingOptions}
                >
                  <option value="">
                    {loadingOptions
                      ? "Đang tải giáo viên..."
                      : "Chọn giáo viên"}
                  </option>

                  {teachers.map((teacher) => {
                    const teacherId = getTeacherIdentifier(teacher);

                    return (
                      <option key={teacherId} value={teacherId}>
                        {teacher.name || "Giáo viên"}
                      </option>
                    );
                  })}
                </select>
              </label>

              <label>
                <span>Phòng học</span>

                <select
                  value={formData.classroom_id}
                  onChange={(event) =>
                    handleFormChange("classroom_id", event.target.value)
                  }
                  disabled={formLoading || loadingOptions}
                >
                  <option value="">
                    {loadingOptions
                      ? "Đang tải phòng học..."
                      : "Chọn phòng học"}
                  </option>

                  {classrooms.map((classroom) => {
                    const classroomId = classroom.id || classroom.classroom_id;

                    const classroomName =
                      classroom.classroom_name ||
                      classroom.class_name ||
                      classroom.room_name ||
                      classroom.name ||
                      classroomId;

                    return (
                      <option key={classroomId} value={classroomId}>
                        {classroomName}
                      </option>
                    );
                  })}
                </select>
              </label>

              <label>
                <span>Số hàng</span>

                <input
                  type="number"
                  min="1"
                  value={formData.row_number}
                  onChange={(event) =>
                    handleFormChange("row_number", event.target.value)
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Số cột</span>

                <input
                  type="number"
                  min="1"
                  value={formData.column_number}
                  onChange={(event) =>
                    handleFormChange("column_number", event.target.value)
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Trạng thái</span>

                <select
                  value={formData.is_active ? "active" : "inactive"}
                  onChange={(event) =>
                    handleFormChange(
                      "is_active",
                      event.target.value === "active",
                    )
                  }
                  disabled={formLoading}
                >
                  <option value="active">Đang hoạt động</option>

                  <option value="inactive">Ngừng hoạt động</option>
                </select>
              </label>

              {optionsError && (
                <div className="class-form-error">{optionsError}</div>
              )}

              {formError && <div className="class-form-error">{formError}</div>}
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={handleCloseForm}
                disabled={formLoading}
              >
                Hủy
              </button>

              <button
                type="button"
                className="add-account-button"
                onClick={handleSubmitClass}
                disabled={formLoading}
              >
                <Icon name="plus" size={17} />

                <span>
                  {formLoading
                    ? "Đang lưu..."
                    : editingClass
                      ? "Lưu thay đổi"
                      : "Thêm lớp"}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedClass && (
        <div
          className="class-modal-overlay"
          onClick={() => setSelectedClass(null)}
        >
          <div
            className="class-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>Thông tin lớp học</h2>
                <p>Chi tiết lớp học trong hệ thống.</p>
              </div>

              <button
                type="button"
                className="edit-teacher-close"
                onClick={() => setSelectedClass(null)}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-detail-content">
              <div className="class-detail-avatar">
                <Icon name="school" size={28} />
              </div>

              <div className="class-detail-info">
                <div className="class-detail-item">
                  <span>Tên lớp</span>
                  {selectedClass.class_name}
                </div>

                <div className="class-detail-item">
                  <span>Giáo viên</span>
                  {selectedClass.teacher_name ||
                    getTeacherName(selectedClass.teacher_id) ||
                    "—"}
                </div>

                <div className="class-detail-item">
                  <span>Phòng học cố định</span>
                  {selectedClass.classroom_name ||
                    getClassroomName(selectedClass.classroom_id) ||
                    "—"}
                </div>

                <div className="class-detail-item">
                  <span>Sĩ số</span>
                  {getClassStudentCount(selectedClass) ?? "—"}
                </div>

                <div className="class-detail-item">
                  <span>Mức độ tập trung TB</span>
                  {getAverageEngagement(selectedClass) !== null
                    ? `${getAverageEngagement(selectedClass).toFixed(0)}%`
                    : "Chưa có dữ liệu"}
                </div>

                <div className="class-detail-item">
                  <span>Trạng thái</span>
                  {selectedClass.is_active !== false
                    ? "Đang hoạt động"
                    : "Ngừng hoạt động"}
                </div>
              </div>

              <div className="class-detail-camera">
                <div className="class-detail-camera-header">
                  <div>
                    <span>Camera phòng học</span>
                    <strong>
                      {selectedClass.camera?.is_configured
                        ? selectedClass.camera.name || "Camera"
                        : "Chưa cấu hình"}
                    </strong>
                  </div>

                  <span
                    className={
                      selectedClass.camera?.is_configured &&
                      selectedClass.camera?.status === "online"
                        ? "class-camera-status online"
                        : "class-camera-status offline"
                    }
                  >
                    {selectedClass.camera?.is_configured &&
                    selectedClass.camera?.status === "online"
                      ? "Đang kết nối"
                      : "Chưa kết nối"}
                  </span>
                </div>

                {selectedClass.camera?.is_configured ? (
                  <div className="class-detail-camera-info">
                    <div className="class-detail-camera-item">
                      <span>Địa chỉ IP</span>
                      <strong>{selectedClass.camera.ip_address || "—"}</strong>
                    </div>

                    <div className="class-detail-camera-item">
                      <span>RTSP Port</span>
                      <strong>{selectedClass.camera.rtsp_port || "—"}</strong>
                    </div>
                  </div>
                ) : (
                  <div className="class-detail-camera-empty">
                    <Icon name="alertCircle" size={20} />
                    <span>Phòng học này chưa được cấu hình camera.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={() => setSelectedClass(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedHealth && (
        <div
          className="class-modal-overlay"
          onClick={() => setSelectedHealth(null)}
        >
          <div
            className="class-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>
                  {selectedHealth === "managed"
                    ? "Lớp đang quản lý"
                    : selectedHealth === "healthy"
                      ? "Lớp hoạt động tốt"
                      : "Lớp cần chú ý"}
                </h2>

                <p>Danh sách lớp thuộc nhóm này.</p>
              </div>

              <button
                type="button"
                className="edit-teacher-close"
                onClick={() => setSelectedHealth(null)}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-health-detail">
              <Icon
                name={
                  selectedHealth === "attention" ? "alertCircle" : "checkCircle"
                }
                size={28}
              />

              {selectedHealth === "managed"
                ? managedClasses > 0
                  ? `${managedClasses} lớp đang được quản lý`
                  : "Chưa có lớp học"
                : selectedHealth === "healthy"
                  ? healthyClasses > 0
                    ? `${healthyClasses} lớp hoạt động tốt`
                    : "Chưa có lớp hoạt động tốt"
                  : attentionClasses > 0
                    ? `${attentionClasses} lớp cần chú ý`
                    : "Chưa có lớp cần chú ý"}

              <span>
                {selectedHealth === "managed"
                  ? "Danh sách này được lấy trực tiếp từ dữ liệu lớp học trong hệ thống."
                  : "Phân loại dựa trên mức độ tập trung trung bình của lớp. Dữ liệu sẽ được cập nhật khi hệ thống có dữ liệu giám sát và phân tích."}
              </span>
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={() => setSelectedHealth(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedMatrixClass && (
        <div className="class-modal-overlay" onClick={handleCloseMatrix}>
          <div
            className="class-modal class-matrix-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>Quản lý sĩ số</h2>
                <p>Lớp {selectedMatrixClass.class_name}</p>
              </div>

              <button
                type="button"
                className="edit-teacher-close"
                onClick={handleCloseMatrix}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-modal-content">
              {matrixLoading ? (
                <div className="class-matrix-loading">Đang tải ma trận...</div>
              ) : matrixError ? (
                <div className="class-matrix-error">{matrixError}</div>
              ) : matrixData ? (
                <>
                  <div className="class-matrix-config">
                    <div className="class-matrix-field">
                      <label>
                        <span>Số hàng</span>

                        <input
                          type="number"
                          min="1"
                          value={matrixData.row_number}
                          onChange={(event) =>
                            handleMatrixChange("row_number", event.target.value)
                          }
                          disabled={matrixSaving}
                        />
                      </label>
                    </div>

                    <div className="class-matrix-field">
                      <label>
                        <span>Số cột</span>

                        <input
                          type="number"
                          min="1"
                          value={matrixData.column_number}
                          onChange={(event) =>
                            handleMatrixChange(
                              "column_number",
                              event.target.value,
                            )
                          }
                          disabled={matrixSaving}
                        />
                      </label>
                    </div>
                  </div>

                  <div className="class-matrix-summary">
                    <div>
                      <span>Số hàng</span>
                      <strong>{matrixData.row_number}</strong>
                    </div>

                    <div>
                      <span>Số cột</span>
                      <strong>{matrixData.column_number}</strong>
                    </div>

                    <div>
                      <span>Tổng số chỗ</span>
                      <strong>
                        {Number(matrixData.row_number || 0) *
                          Number(matrixData.column_number || 0)}
                      </strong>
                    </div>
                  </div>

                  <div className="class-matrix-section">
                    <div className="class-matrix-section-header">
                      <div>
                        <h3>Ma trận chỗ ngồi</h3>

                        <p>Mỗi ô tương ứng với một vị trí học sinh.</p>
                      </div>
                    </div>

                    <div className="class-matrix-preview">
                      <div
                        className="class-seat-grid"
                        style={{
                          gridTemplateColumns: `repeat(${matrixData.column_number}, minmax(70px, 1fr))`,
                        }}
                      >
                        {Array.from(
                          {
                            length:
                              Number(matrixData.row_number) *
                              Number(matrixData.column_number),
                          },
                          (_, index) => {
                            const seatNumber = index + 1;

                            const seat = matrixData.seats?.find(
                              (item) =>
                                Number(item.seat_number) === seatNumber ||
                                item.seat_id === `S${seatNumber}`,
                            );

                            return (
                              <div
                                key={seatNumber}
                                className={
                                  seat?.student_id
                                    ? "class-seat occupied"
                                    : "class-seat"
                                }
                              >
                                <strong>
                                  {seat?.seat_id || `S${seatNumber}`}
                                </strong>

                                <span>{seat?.student_id || "Trống"}</span>
                              </div>
                            );
                          },
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={handleCloseMatrix}
                disabled={matrixSaving}
              >
                Hủy
              </button>

              <button
                type="button"
                className="add-account-button"
                onClick={handleSaveMatrix}
                disabled={matrixLoading || matrixSaving || !matrixData}
              >
                <Icon name="checkCircle" size={17} />

                <span>{matrixSaving ? "Đang lưu..." : "Lưu ma trận"}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDeleteClass && (
        <ConfirmModal
          title="Xác nhận xóa lớp"
          message={`Bạn có chắc muốn xóa lớp "${confirmDeleteClass.class_name}" không?`}
          confirmText="Xóa lớp"
          cancelText="Hủy"
          onConfirm={() => handleDeleteClass(confirmDeleteClass)}
          onCancel={() => setConfirmDeleteClass(null)}
        />
      )}
    </>
  );
};

export default ClassManagementPanel;
