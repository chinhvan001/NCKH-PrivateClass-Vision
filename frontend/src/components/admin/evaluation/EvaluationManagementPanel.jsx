import { useMemo, useState } from "react";

import Icon from "../../common/Icon";

const MOCK_CLASSES = [
  {
    id: "class-11b2",
    name: "11B2",
    subject: "Toán",
    teacher: "Nguyễn Văn An",
    classroom: "A204",
    students: 42,
    engagement: 82,
    attention: 85,
    sessions: 18,
    trend: 4,
    status: "stable",
    attentionStudents: 5,
  },
  {
    id: "class-10a1",
    name: "10A1",
    subject: "Vật lý",
    teacher: "Trần Minh Hoàng",
    classroom: "B102",
    students: 38,
    engagement: 87,
    attention: 89,
    sessions: 16,
    trend: 6,
    status: "good",
    attentionStudents: 2,
  },
  {
    id: "class-10a2",
    name: "10A2",
    subject: "Hóa học",
    teacher: "Lê Thu Hà",
    classroom: "B103",
    students: 41,
    engagement: 76,
    attention: 79,
    sessions: 17,
    trend: -3,
    status: "attention",
    attentionStudents: 8,
  },
  {
    id: "class-10a3",
    name: "10A3",
    subject: "Ngữ văn",
    teacher: "Phạm Thị Mai",
    classroom: "A105",
    students: 40,
    engagement: 84,
    attention: 87,
    sessions: 19,
    trend: 2,
    status: "good",
    attentionStudents: 3,
  },
  {
    id: "class-11a1",
    name: "11A1",
    subject: "Tiếng Anh",
    teacher: "Đỗ Minh Anh",
    classroom: "C201",
    students: 39,
    engagement: 79,
    attention: 82,
    sessions: 15,
    trend: 1,
    status: "stable",
    attentionStudents: 6,
  },
  {
    id: "class-11a3",
    name: "11A3",
    subject: "Sinh học",
    teacher: "Nguyễn Thị Lan",
    classroom: "C203",
    students: 37,
    engagement: 91,
    attention: 93,
    sessions: 18,
    trend: 8,
    status: "good",
    attentionStudents: 1,
  },
];

const STATUS_CONFIG = {
  good: {
    label: "Tốt",
    className: "evaluation-status-good",
  },
  stable: {
    label: "Ổn định",
    className: "evaluation-status-stable",
  },
  attention: {
    label: "Cần chú ý",
    className: "evaluation-status-attention",
  },
};

const EvaluationManagementPanel = () => {
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [teacherFilter, setTeacherFilter] = useState("all");
  const [periodFilter, setPeriodFilter] = useState("month");

  const subjects = useMemo(() => {
    return [...new Set(MOCK_CLASSES.map((item) => item.subject))];
  }, []);

  const teachers = useMemo(() => {
    return [...new Set(MOCK_CLASSES.map((item) => item.teacher))];
  }, []);

  const filteredClasses = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return MOCK_CLASSES.filter((item) => {
      const matchesSearch =
        !keyword ||
        item.name.toLowerCase().includes(keyword) ||
        item.subject.toLowerCase().includes(keyword) ||
        item.teacher.toLowerCase().includes(keyword);

      const matchesSubject =
        subjectFilter === "all" ||
        item.subject === subjectFilter;

      const matchesTeacher =
        teacherFilter === "all" ||
        item.teacher === teacherFilter;

      return (
        matchesSearch &&
        matchesSubject &&
        matchesTeacher
      );
    });
  }, [search, subjectFilter, teacherFilter]);

  const totalClasses = MOCK_CLASSES.length;

  const activeClasses = MOCK_CLASSES.filter(
    (item) => item.sessions > 0
  ).length;

  const averageEngagement = Math.round(
    MOCK_CLASSES.reduce(
      (total, item) => total + item.engagement,
      0
    ) / MOCK_CLASSES.length
  );

  const attentionClassCount = MOCK_CLASSES.filter(
    (item) => item.status === "attention"
  ).length;

  const totalStudents = MOCK_CLASSES.reduce(
    (total, item) => total + item.students,
    0
  );

  const handleViewClass = (classItem) => {
    console.log("View evaluation:", classItem);
  };

  const handleResetFilters = () => {
    setSearch("");
    setSubjectFilter("all");
    setTeacherFilter("all");
    setPeriodFilter("month");
  };

  return (
    <section className="evaluation-page">
      {/* PAGE HEADER */}
      <div className="evaluation-page-header">
        <div>
          <div className="evaluation-title-row">
            <div className="evaluation-title-icon">
              <Icon name="activity" size={22} />
            </div>

            <div>
              <h1>Phân tích & đánh giá</h1>

              <p>
                Theo dõi mức độ tập trung và tham gia
                của học sinh theo từng lớp học.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FILTERS */}
      <div className="evaluation-filter-card">
        <div className="evaluation-filter-item">
          <label>Chọn môn học</label>

          <select
            value={subjectFilter}
            onChange={(event) =>
              setSubjectFilter(event.target.value)
            }
          >
            <option value="all">Tất cả môn học</option>

            {subjects.map((subject) => (
              <option
                key={subject}
                value={subject}
              >
                {subject}
              </option>
            ))}
          </select>
        </div>

        <div className="evaluation-filter-item">
          <label>Giáo viên</label>

          <select
            value={teacherFilter}
            onChange={(event) =>
              setTeacherFilter(event.target.value)
            }
          >
            <option value="all">
              Tất cả giáo viên
            </option>

            {teachers.map((teacher) => (
              <option
                key={teacher}
                value={teacher}
              >
                {teacher}
              </option>
            ))}
          </select>
        </div>

        <div className="evaluation-filter-item">
          <label>Khoảng thời gian</label>

          <select
            value={periodFilter}
            onChange={(event) =>
              setPeriodFilter(event.target.value)
            }
          >
            <option value="week">Tuần này</option>
            <option value="month">Tháng này</option>
            <option value="semester">Học kỳ</option>
          </select>
        </div>

        <div className="evaluation-search">
          <Icon name="search" size={18} />

          <input
            type="text"
            placeholder="Tìm lớp học, môn học..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </div>

        <button
          type="button"
          className="evaluation-reset-button"
          onClick={handleResetFilters}
        >
          <Icon name="refresh" size={17} />
          <span>Làm mới</span>
        </button>
      </div>

      {/* OVERVIEW STATS */}
      <div className="evaluation-stat-grid">
        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon blue">
            <Icon name="building" size={21} />
          </div>

          <div>
            <span>Tổng số lớp</span>
            <div>{totalClasses}</div>
            <small>{totalStudents} học sinh</small>
          </div>
        </div>

        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon green">
            <Icon name="checkCircle" size={21} />
          </div>

          <div>
            <span>Lớp có dữ liệu</span>
            <div>{activeClasses}</div>
            <small>Đang được theo dõi</small>
          </div>
        </div>

        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon purple">
            <Icon name="trendingUp" size={21} />
          </div>

          <div>
            <span>Tham gia trung bình</span>
            <div>{averageEngagement}%</div>
            <small>Toàn bộ lớp học</small>
          </div>
        </div>

        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon orange">
            <Icon name="alertCircle" size={21} />
          </div>

          <div>
            <span>Lớp cần chú ý</span>
            <div>{attentionClassCount}</div>
            <small>Cần giáo viên theo dõi</small>
          </div>
        </div>
      </div>

      {/* CLASS LIST */}
      <div className="evaluation-section">
        <div className="evaluation-section-header">
          <div>
            <h2>Các lớp học</h2>

            <p>
              Chọn một lớp để xem chi tiết mức độ
              tập trung và tham gia của học sinh.
            </p>
          </div>

          <span className="evaluation-result-count">
            {filteredClasses.length} lớp
          </span>
        </div>

        {filteredClasses.length === 0 ? (
          <div className="evaluation-empty">
            <Icon name="search" size={28} />

            <h3>Không tìm thấy lớp học</h3>

            <p>
              Không có lớp học nào phù hợp với bộ lọc
              hiện tại.
            </p>

            <button
              type="button"
              onClick={handleResetFilters}
            >
              Xóa bộ lọc
            </button>
          </div>
        ) : (
          <div className="evaluation-class-grid">
            {filteredClasses.map((classItem) => {
              const status =
                STATUS_CONFIG[classItem.status];

              return (
                <article
                  key={classItem.id}
                  className="evaluation-class-card"
                >
                  <div className="evaluation-class-card-header">
                    <div>
                      <span className="evaluation-class-name">
                        {classItem.name}
                      </span>

                      <span className="evaluation-class-subject">
                        {classItem.subject}
                      </span>
                    </div>

                    <span
                      className={`evaluation-status ${status.className}`}
                    >
                      {status.label}
                    </span>
                  </div>

                  <div className="evaluation-class-info">
                    <div>
                      <Icon name="user" size={16} />
                      <span>
                        Giáo viên: {classItem.teacher}
                      </span>
                    </div>

                    <div>
                      <Icon name="building" size={16} />
                      <span>
                        Phòng {classItem.classroom}
                      </span>
                    </div>

                    <div>
                      <Icon name="users" size={16} />
                      <span>
                        {classItem.students} học sinh
                      </span>
                    </div>
                  </div>

                  <div className="evaluation-progress-block">
                    <div className="evaluation-progress-header">
                      <span>Mức độ tham gia</span>

                      <span>
                        {classItem.engagement}%
                      </span>
                    </div>

                    <div className="evaluation-progress">
                      <div
                        className="evaluation-progress-value"
                        style={{
                          width: `${classItem.engagement}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="evaluation-class-metrics">
                    <div>
                      <span>Tập trung</span>
                      <span>
                        {classItem.attention}%
                      </span>
                    </div>

                    <div>
                      <span>Phiên học</span>
                      <span>
                        {classItem.sessions}
                      </span>
                    </div>

                    <div>
                      <span>Cần chú ý</span>
                      <span>
                        {classItem.attentionStudents}
                      </span>
                    </div>
                  </div>

                  <div className="evaluation-class-footer">
                    <span
                      className={
                        classItem.trend >= 0
                          ? "evaluation-trend-up"
                          : "evaluation-trend-down"
                      }
                    >
                      <Icon
                        name={
                          classItem.trend >= 0
                            ? "arrowUp"
                            : "arrowDown"
                        }
                        size={15}
                      />

                      {classItem.trend >= 0 ? "+" : ""}
                      {classItem.trend}%
                    </span>

                    <button
                      type="button"
                      onClick={() =>
                        handleViewClass(classItem)
                      }
                    >
                      Xem phân tích

                      <Icon
                        name="chevronRight"
                        size={16}
                      />
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
};

export default EvaluationManagementPanel;