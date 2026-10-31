import { useMemo, useState, useEffect } from "react";
import { 
  Layers, 
  Activity, 
  AlertTriangle, 
  Search, 
  RefreshCw, 
  Eye, 
  ArrowLeft, 
  AlertCircle, 
  Loader2
} from "lucide-react";

import { getAuthHeaders } from "../../../utils/AuthSession";

const STATUS_CONFIG = {
  good: { label: "Tốt", classType: "status-good" },
  stable: { label: "Ổn định", classType: "status-stable" },
  attention: { label: "Cần chú ý", classType: "status-attention" },
};

// Dữ liệu camera AI của từng tiết (data_status từ backend)
const DATA_STATUS = {
  complete: { label: "Đầy đủ", classType: "status-good" },
  partial: { label: "Bị gián đoạn", classType: "status-attention" },
  pending: { label: "Đang chốt kết quả", classType: "status-stable" },
  live: { label: "Đang giám sát", classType: "status-stable" },
  no_data: { label: "Không có dữ liệu", classType: "status-stable" },
};

const EvaluationManagementPanel = () => {
  const [classesData, setClassesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedClassId, setSelectedClassId] = useState(null);
  const [classDetail, setClassDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");

  const fetchEvaluations = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/evaluations/classes-overview', { headers: await getAuthHeaders() });
      const result = await response.json();
      if (result.success) {
        setClassesData(result.data);
        setError(null);
      } else {
        setError(result.error || "Lỗi từ server.");
      }
    } catch (err) {
      setError("Không thể kết nối đến máy chủ.");
    } finally {
      setLoading(false);
    }
  };

  const fetchClassDetail = async (classId) => {
    setSelectedClassId(classId);
    setLoadingDetail(true);
    
    try {
      const response = await fetch(`/api/v1/evaluations/classes/${classId}/details`, { headers: await getAuthHeaders() });
      const result = await response.json();
      if (result.success) {
        setClassDetail(result.data);
      } else {
        alert(result.error || "Không thể tải chi tiết lớp học.");
        setSelectedClassId(null);
      }
    } catch (err) {
      alert("Lỗi kết nối khi tải chi tiết lớp học.");
      setSelectedClassId(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    if (!selectedClassId) {
      fetchEvaluations();
    }
  }, [selectedClassId]);

  const subjects = useMemo(() => [...new Set(classesData.map((item) => item.subject))], [classesData]);

  const filteredClasses = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return classesData.filter((item) => {
      const matchesSearch = !keyword || item.name.toLowerCase().includes(keyword) || 
                            item.teacher.toLowerCase().includes(keyword);
      const matchesSubject = subjectFilter === "all" || item.subject === subjectFilter;
      return matchesSearch && matchesSubject;
    });
  }, [classesData, search, subjectFilter]);

  const totalClasses = classesData.length;
  const attentionCount = classesData.filter((item) => item.status === "attention").length;

  const overallClassAvgConcentration = useMemo(() => {
    if (classesData.length === 0) return 0;
    const total = classesData.reduce((acc, curr) => acc + (curr.attention || 0), 0);
    return (total / classesData.length).toFixed(1);
  }, [classesData]);

  const classAverageScore = useMemo(() => {
    if (!classDetail || !classDetail.students || classDetail.students.length === 0) return 0;
    const total = classDetail.students.reduce((acc, s) => acc + (s.attention_score || 0), 0);
    return (total / classDetail.students.length).toFixed(1);
  }, [classDetail]);

  if (loading && classesData.length === 0 && !selectedClassId) {
    return (
      <div className="evaluation-page flex items-center justify-center min-h-screen">
        <Loader2 size={32} className="animate-spin text-gray-400" />
      </div>
    );
  }

  if (error && !selectedClassId) {
    return (
      <div className="evaluation-page">
        <div className="system-error-state">
            <AlertCircle size={42} className="system-error-icon" />
            <h3>Đã xảy ra lỗi</h3>
            <p>{error}</p>
            <button onClick={fetchEvaluations} className="system-btn-retry">Thử lại</button>
        </div>
      </div>
    );
  }

  // Giao diện chi tiết báo cáo từng lớp học
  if (selectedClassId) {
    return (
      <div className="evaluation-page">
        <div style={{ marginBottom: '20px' }}>
          <button 
            onClick={() => { setSelectedClassId(null); setClassDetail(null); }}
            className="evaluation-btn-reset"
          >
            <ArrowLeft size={16} />
            Quay lại danh sách lớp
          </button>
        </div>

        {loadingDetail ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 size={32} className="animate-spin text-gray-400" />
          </div>
        ) : classDetail ? (
          <>
            <div className="evaluation-page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h1>{classDetail.class_name}</h1>
                <p>Môn học: <strong>{classDetail.subject}</strong> | Giáo viên: <strong>{classDetail.teacher}</strong> | Phòng: <strong>{classDetail.classroom}</strong></p>
              </div>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div className="evaluation-stat-card" style={{ padding: '12px 20px', minWidth: '160px' }}>
                  <div className="evaluation-stat-content">
                    <span>Mức độ tập trung TB cả lớp</span>
                    <strong style={{ color: '#0f172a', fontSize: '1.25rem' }}>{classAverageScore}%</strong>
                  </div>
                </div>
                <div className="evaluation-stat-card" style={{ padding: '12px 20px', minWidth: '160px' }}>
                  <div className="evaluation-stat-content">
                    <span>Tổng số học sinh ghi nhận</span>
                    <strong>{classDetail.students.length} em</strong>
                  </div>
                </div>
                <div className="evaluation-stat-card" style={{ padding: '12px 20px', minWidth: '160px' }}>
                  <div className="evaluation-stat-content">
                    <span>Tiết bị gián đoạn</span>
                    <strong>
                      {classDetail.sessions.filter((row) => row.data_status === "partial").length}/{classDetail.sessions.length} tiết
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="evaluation-main-container" style={{ marginTop: '20px' }}>
              <div className="evaluation-section-header">
                <h2>Báo cáo mức độ tập trung chi tiết</h2>
                <p>Mức tập trung trung bình của từng học sinh qua các tiết, theo thời gian camera AI quan sát được.</p>
              </div>

              <div className="evaluation-table-wrapper">
                <table className="evaluation-table">
                  <thead>
                    <tr>
                      <th>STT</th>
                      <th>Họ và tên học sinh</th>
                      <th>Mức độ tập trung trung bình</th>
                      <th>Đánh giá chung</th>
                    </tr>
                  </thead>
                  <tbody>
                    {classDetail.students.length === 0 ? (
                      <tr>
                        <td colSpan="4" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                          Chưa có dữ liệu giám sát nào của camera AI cho lớp này.
                        </td>
                      </tr>
                    ) : (
                      classDetail.students.map((student, index) => {
                        const statusInfo = STATUS_CONFIG[student.status] || STATUS_CONFIG.stable;
                        return (
                          <tr key={student.student_id}>
                            <td>{index + 1}</td>
                            <td><strong>{student.name}</strong></td>
                            <td><strong style={{ color: '#0f172a' }}>{student.attention_score}%</strong></td>
                            <td>
                              <span className={`status-badge ${statusInfo.classType}`}>
                                <span className="dot"></span>
                                {statusInfo.label}
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="evaluation-main-container" style={{ marginTop: '20px' }}>
              <div className="evaluation-section-header">
                <h2>Các tiết đã giám sát</h2>
                <p>Tiết bị gián đoạn (camera AI tắt hoặc khởi động lại giữa tiết) chỉ có dữ liệu cho một phần tiết học.</p>
              </div>

              <div className="evaluation-table-wrapper">
                <table className="evaluation-table">
                  <thead>
                    <tr>
                      <th>Ngày</th>
                      <th>Giờ</th>
                      <th>Môn học</th>
                      <th>Số ghế có dữ liệu</th>
                      <th>Mức độ tập trung trung bình</th>
                      <th>Dữ liệu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {classDetail.sessions.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                          Chưa có tiết nào được giám sát.
                        </td>
                      </tr>
                    ) : (
                      classDetail.sessions.map((row) => {
                        const dataInfo = DATA_STATUS[row.data_status] || DATA_STATUS.no_data;
                        return (
                          <tr key={row.id}>
                            <td>{row.session_date || '--'}</td>
                            <td>{row.start_time || '--'}</td>
                            <td>{row.subject || '--'}</td>
                            <td>{row.seats}</td>
                            <td><strong style={{ color: '#0f172a' }}>{row.attention != null ? `${row.attention}%` : '--'}</strong></td>
                            <td>
                              <span className={`status-badge ${dataInfo.classType}`}>
                                <span className="dot"></span>
                                {dataInfo.label}
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : null}
      </div>
    );
  }

  // Giao diện tổng quan danh sách lớp (Dashboard)
  return (
    <div className="evaluation-page">
      <div className="evaluation-page-header">
        <h1>Phân tích & Đánh giá (Dashboard)</h1>
        <p>Tổng hợp từ đánh giá theo ghế mà camera AI ghi sau mỗi tiết học.</p>
      </div>

      {/* 3 Thẻ thống kê với Icon Lucide đã được cập nhật chuẩn ngữ nghĩa */}
      <div className="evaluation-stat-grid">
        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon blue">
            <Layers size={22} />
          </div>
          <div className="evaluation-stat-content">
            <span>Tổng số lớp</span>
            <strong>{totalClasses}</strong>
          </div>
        </div>

        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon green">
            <Activity size={22} />
          </div>
          <div className="evaluation-stat-content">
            <span>Độ tập trung TB toàn hệ thống</span>
            <strong>{overallClassAvgConcentration}%</strong>
          </div>
        </div>

        <div className="evaluation-stat-card">
          <div className="evaluation-stat-icon orange">
            <AlertTriangle size={22} />
          </div>
          <div className="evaluation-stat-content">
            <span>Lớp cần chú ý</span>
            <strong>{attentionCount}</strong>
          </div>
        </div>
      </div>

      <div className="evaluation-main-container">
        <div className="evaluation-section-header">
          <h2>Báo cáo danh sách lớp học</h2>
          <p>Hiển thị hiệu suất tập trung trung bình toàn lớp.</p>
        </div>

        <div className="evaluation-filters">
          <div className="evaluation-search-wrapper">
            <Search size={18} className="evaluation-search-icon" />
            <input 
              type="text" 
              placeholder="Tìm theo tên lớp, giáo viên..." 
              className="evaluation-search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            className="evaluation-select"
            value={subjectFilter}
            onChange={(e) => setSubjectFilter(e.target.value)}
          >
            <option value="all">Tất cả môn học</option>
            {subjects.map(sub => <option key={sub} value={sub}>{sub}</option>)}
          </select>
          <button type="button" className="evaluation-btn-reset" onClick={fetchEvaluations}>
            <RefreshCw size={16} />
            Làm mới
          </button>
        </div>

        <div className="evaluation-table-wrapper">
          <table className="evaluation-table">
            <thead>
              <tr>
                <th>Tên lớp</th>
                <th>Số học sinh ghi nhận</th>
                <th>Giáo viên</th>
                <th>Mức độ tập trung trung bình</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredClasses.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
                    Không tìm thấy dữ liệu báo cáo lớp học phù hợp.
                  </td>
                </tr>
              ) : (
                filteredClasses.map((item) => {
                  const statusInfo = STATUS_CONFIG[item.status] || STATUS_CONFIG.stable;
                  return (
                    <tr key={item.id}>
                      <td><strong>{item.name}</strong></td>
                      <td>{item.students}</td>
                      <td>{item.teacher}</td>
                      <td><strong style={{ color: '#0f172a' }}>{item.attention}%</strong></td>
                      <td>
                        <span className={`status-badge ${statusInfo.classType}`}>
                          <span className="dot"></span>
                          {statusInfo.label}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <button 
                            className="btn-action-icon" 
                            title="Xem chi tiết báo cáo"
                            onClick={() => fetchClassDetail(item.id)}
                          >
                            <Eye size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default EvaluationManagementPanel;