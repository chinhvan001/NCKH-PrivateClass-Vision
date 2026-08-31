import { useMemo, useState } from "react";
import Icon from "../common/Icon";

const AccountManagementPanel = ({
  users = [],
  loading = false,
  onRefresh,
}) => {
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  // ========================================
  // Chuẩn hóa dữ liệu teacher
  // ========================================

  const teachers = useMemo(() => {
    return users.map((user) => {
      // subject từ API là array
      // Ví dụ: ["Toán", "Vật Lý"]
      let subjects = [];

      if (Array.isArray(user.subject)) {
        subjects = user.subject;
      } else if (user.subject) {
        subjects = [user.subject];
      }

      return {
        id: user.id || user.uid,
        email: user.email || "Chưa có email",
        name: user.name || "Chưa cập nhật",
        phoneNumber: user.phone_number || "--",
        subject: subjects,

        isActive:
          user.is_active ??
          user.isActive ??
          true,
      };
    });
  }, [users]);

  // ========================================
  // Danh sách tất cả môn học
  // ========================================

  const subjects = useMemo(() => {
    const uniqueSubjects = new Set();

    teachers.forEach((teacher) => {
      teacher.subject.forEach((subject) => {
        if (subject) {
          uniqueSubjects.add(subject);
        }
      });
    });

    return [...uniqueSubjects];
  }, [teachers]);

  // ========================================
  // Filter
  // ========================================

  const filteredTeachers = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return teachers.filter((teacher) => {
      // Tìm theo tên, email hoặc số điện thoại
      const matchSearch =
        !keyword ||
        teacher.name.toLowerCase().includes(keyword) ||
        teacher.email.toLowerCase().includes(keyword) ||
        teacher.phoneNumber.toLowerCase().includes(keyword);

      // Giáo viên có thể có nhiều môn
      const matchSubject =
        subjectFilter === "all" ||
        teacher.subject.includes(subjectFilter);

      // Lọc trạng thái
      const matchStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && teacher.isActive) ||
        (statusFilter === "inactive" && !teacher.isActive);

      return (
        matchSearch &&
        matchSubject &&
        matchStatus
      );
    });
  }, [
    teachers,
    search,
    subjectFilter,
    statusFilter,
  ]);

  // ========================================
  // Statistics
  // ========================================

  const totalTeachers = teachers.length;

  const activeTeachers = teachers.filter(
    (teacher) => teacher.isActive
  ).length;

  const inactiveTeachers =
    totalTeachers - activeTeachers;

  // ========================================
  // Refresh
  // ========================================

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  return (
    <>
      {/* ========================================
          STATISTICS
      ======================================== */}

      <section className="account-stats-section">
        <h2>Tài khoản giáo viên</h2>

        <div className="account-stats-grid">

          {/* Tổng giáo viên */}

          <article className="account-stat-card blue">
            <div className="account-stat-icon">
              <Icon name="user" size={21} />
            </div>

            <div>
              <span>Tổng giáo viên</span>
              <strong>{totalTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          {/* Đang hoạt động */}

          <article className="account-stat-card green">
            <div className="account-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>

            <div>
              <span>Đang hoạt động</span>
              <strong>{activeTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          {/* Đã vô hiệu hóa */}

          <article className="account-stat-card red">
            <div className="account-stat-icon">
              <Icon name="xCircle" size={21} />
            </div>

            <div>
              <span>Đã vô hiệu hóa</span>
              <strong>{inactiveTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          {/* Bộ môn */}

          <article className="account-stat-card purple">
            <div className="account-stat-icon">
              <Icon name="school" size={21} />
            </div>

            <div>
              <span>Bộ môn</span>
              <strong>{subjects.length}</strong>
              <small>Môn học</small>
            </div>
          </article>

          {/* Sắp có thêm */}

          <article className="account-stat-card add-stat-card">
            <div className="account-stat-icon">
              <Icon name="plus" size={22} />
            </div>

            <div>
              <strong>Sắp có thêm</strong>
              <small>Tính năng sắp cập nhật</small>
            </div>
          </article>

        </div>
      </section>

      {/* ========================================
          MANAGEMENT
      ======================================== */}

      <section className="account-panel">

        {/* HEADER */}

        <div className="account-panel-heading">
          <div>
            <h2>Quản lý tài khoản giáo viên</h2>

            <p>
              Danh sách tài khoản giáo viên trong hệ thống.
            </p>
          </div>

          <button
            type="button"
            className="add-account-button"
          >
            <Icon name="plus" size={17} />
            <span>Thêm giáo viên</span>
          </button>
        </div>

        {/* ========================================
            FILTERS
        ======================================== */}

        <div className="account-filters">

          {/* SEARCH */}

          <div className="account-search">
            <input
              type="text"
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
              placeholder="Tìm kiếm theo tên..."
            />

            <span className="account-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          {/* SUBJECT */}

          <label className="account-select">
            <span>Bộ môn</span>

            <select
              value={subjectFilter}
              onChange={(e) =>
                setSubjectFilter(e.target.value)
              }
            >
              <option value="all">
                Tất cả bộ môn
              </option>

              {subjects.map((subject) => (
                <option
                  key={subject}
                  value={subject}
                >
                  {subject}
                </option>
              ))}
            </select>
          </label>

          {/* STATUS */}

          <label className="account-select">
            <span>Trạng thái</span>

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value)
              }
            >
              <option value="all">
                Tất cả trạng thái
              </option>

              <option value="active">
                Đang hoạt động
              </option>

              <option value="inactive">
                Đã vô hiệu hóa
              </option>
            </select>
          </label>

          {/* REFRESH */}

          <button
            type="button"
            className="refresh-button"
            onClick={handleRefresh}
          >
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        {/* ========================================
            TABLE
        ======================================== */}

        <div className="account-table-wrap">
          <table className="account-table">

            <thead>
              <tr>
                <th>Tên giáo viên</th>
                <th>Gmail</th>
                <th>Số điện thoại</th>
                <th>Bộ môn</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>

              {/* LOADING */}

              {loading ? (
                <tr>
                  <td
                    colSpan="6"
                    className="table-empty"
                  >
                    Đang tải danh sách giáo viên...
                  </td>
                </tr>
              ) : filteredTeachers.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="table-empty"
                  >
                    Không tìm thấy tài khoản giáo viên.
                  </td>
                </tr>
              ) : (

                /* DATA */

                filteredTeachers.map((teacher) => (
                  <tr
                    key={
                      teacher.id ||
                      teacher.email
                    }
                  >

                    {/* TÊN */}

                    <td>
                      <div className="account-cell">

                        <div className="table-avatar">
                          <Icon
                            name="user"
                            size={19}
                          />
                        </div>

                        <div>
                          <strong>
                            {teacher.name}
                          </strong>

                          <span>
                            Giáo viên
                          </span>
                        </div>

                      </div>
                    </td>

                    {/* GMAIL */}

                    <td>
                      <span className="account-email">
                        {teacher.email}
                      </span>
                    </td>

                    {/* SỐ ĐIỆN THOẠI */}

                    <td>
                      <span className="account-phone">
                        {teacher.phoneNumber}
                      </span>
                    </td>

                    {/* BỘ MÔN */}

                    <td>
                      <div className="account-subject-list">

                        {teacher.subject.length > 0 ? (
                          teacher.subject.map(
                            (subject, index) => (
                              <span
                                key={`${subject}-${index}`}
                                className="account-subject-tag"
                              >
                                {subject}
                              </span>
                            )
                          )
                        ) : (
                          <span className="account-subject-empty">
                            Chưa cập nhật
                          </span>
                        )}

                      </div>
                    </td>

                    {/* STATUS */}

                    <td>
                      <span
                        className={`status-badge ${
                          teacher.isActive
                            ? "active"
                            : "inactive"
                        }`}
                      >
                        <i />

                        {teacher.isActive
                          ? "Đang hoạt động"
                          : "Đã vô hiệu hóa"}
                      </span>
                    </td>

                    {/* ACTION */}

                    <td>
                      <div className="row-actions">

                        <button
                          type="button"
                          aria-label={`Chỉnh sửa ${teacher.email}`}
                        >
                          <Icon
                            name="edit"
                            size={17}
                          />
                        </button>

                        <button
                          type="button"
                          aria-label={`Thao tác với ${teacher.email}`}
                        >
                          <Icon
                            name="more"
                            size={18}
                          />
                        </button>

                      </div>
                    </td>

                  </tr>
                ))
              )}

            </tbody>
          </table>
        </div>

        {/* ========================================
            PAGINATION
        ======================================== */}

        <div className="account-pagination">
          <span>
            Hiển thị {filteredTeachers.length} giáo viên
          </span>

          <div>
            <button
              type="button"
              disabled
            >
              <Icon
                name="first"
                size={15}
              />
            </button>

            <button
              type="button"
              disabled
            >
              <Icon
                name="arrowLeft"
                size={15}
              />
            </button>

            <button
              type="button"
              className="current-page"
            >
              1
            </button>

            <button type="button">
              <Icon
                name="arrowRight"
                size={15}
              />
            </button>

            <button type="button">
              <Icon
                name="last"
                size={15}
              />
            </button>
          </div>
        </div>

      </section>
    </>
  );
};

export default AccountManagementPanel;