import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  FileText, Search, RefreshCw, Eye, Trash2, CheckCircle, AlertCircle, MessageSquare, HelpCircle, ChevronLeft, ChevronRight, Archive, X
} from 'lucide-react';

export default function ReportManagementPanel() {
  const [reports, setReports] = useState([]);
  const [classList, setClassList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [activeTab, setActiveTab] = useState('student_note');
  const [selectedGradeFilter, setSelectedGradeFilter] = useState('');
  const [selectedClassFilter, setSelectedClassFilter] = useState('');

  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;
  const tableTopRef = useRef(null);

  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedStudentDetail, setSelectedStudentDetail] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const cachedData = sessionStorage.getItem('app_reports_cache_data');
    if (cachedData) {
      try {
        const parsed = JSON.parse(cachedData);
        setReports(parsed.data || []);
        if (parsed.classes) setClassList(parsed.classes);
      } catch (e) {}
    }

    fetchReportsInBackground(true);
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, selectedGradeFilter, selectedClassFilter, searchTerm]);

  const fetchReportsInBackground = async (isBackground = false) => {
    if (!isBackground || reports.length === 0) {
      setLoading(true);
    }
    try {
      const response = await fetch('/api/v1/reports');
      const result = await response.json();
      if (result.success) {
        setReports(result.data || []);
        sessionStorage.setItem('app_reports_cache_data', JSON.stringify(result));
      }

      const studentRes = await fetch('/api/v1/students');
      const studentData = await studentRes.json();
      if (studentData.success && studentData.classes) {
        setClassList(studentData.classes);
      }
    } catch (error) {
      console.error('Lỗi tải ngầm dữ liệu báo cáo:', error);
    } finally {
      setLoading(false);
    }
  };

  const showNotify = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Hàm mở Modal chi tiết và lấy toàn bộ thông tin học sinh kèm danh sách ghi chú
  const handleOpenDetail = async (report) => {
    try {
      const res = await fetch(`/api/v1/students/${report.student_id}`);
      const result = await res.json();
      if (result.success) {
        setSelectedStudentDetail(result.data);
      } else {
        setSelectedStudentDetail({
          full_name: report.student_name,
          current_class: report.current_class,
          notes: [{ teacher_name: report.teacher_name, subject: report.subject, content: report.content, created_at: report.created_at }]
        });
      }
    } catch (e) {
      setSelectedStudentDetail({
        full_name: report.student_name,
        current_class: report.current_class,
        notes: [{ teacher_name: report.teacher_name, subject: report.subject, content: report.content }]
      });
    }
    setShowDetailModal(true);
  };

  const handleDeleteReport = async (studentId, reportId) => {
    if (!reportId) return;
    if (!window.confirm('Bạn có chắc chắn muốn xóa bản ghi này?')) return;
    try {
      const res = await fetch(`/api/v1/students/${studentId}/reports/${reportId}`, { method: 'DELETE' });
      const result = await res.json();
      if (result.success) {
        showNotify('Đã xóa thành công!');
        sessionStorage.removeItem('app_reports_cache_data');
        fetchReportsInBackground(false);
        setShowDetailModal(false);
      } else {
        showNotify(result.error || 'Xóa thất bại', 'error');
      }
    } catch (err) {
      showNotify('Lỗi kết nối máy chủ', 'error');
    }
  };

  // Sắp xếp A-Z theo tên chính (từ cuối cùng) và gắn STT cố định toàn trường
  const sortedAndIndexedReports = useMemo(() => {
    const parseFullName = (name) => {
      const trimmed = (name || "").trim();
      if (!trimmed) return { firstName: "zzz", fullName: "" };
      const parts = trimmed.split(/\s+/);
      return { firstName: parts[parts.length - 1], fullName: trimmed };
    };

    const sorted = [...reports].sort((a, b) => {
      const pA = parseFullName(a.student_name);
      const pB = parseFullName(b.student_name);
      const cmp = pA.firstName.localeCompare(pB.firstName, 'vi', { sensitivity: 'accent', numeric: true });
      if (cmp !== 0) return cmp;
      return pA.fullName.localeCompare(pB.fullName, 'vi', { sensitivity: 'accent', numeric: true });
    });

    return sorted.map((item, index) => ({
      ...item,
      originalIndex: index + 1 // STT cố định theo danh sách gốc A-Z
    }));
  }, [reports]);

  // Thống kê 3 thẻ
  const stats = useMemo(() => {
    const teacherNotes = reports.filter(r => (r.type || 'student_note') === 'student_note' && r.has_note).length;
    const systemIssues = reports.filter(r => (r.type || 'student_note') === 'system_issue').length;
    const userFeedbacks = reports.filter(r => (r.type || 'student_note') === 'user_feedback').length;
    return { teacherNotes, systemIssues, userFeedbacks };
  }, [reports]);

  // Lọc dữ liệu theo Tab, Từ khóa và Lớp
  const filteredReports = useMemo(() => {
    const keyword = searchTerm.trim().toLowerCase();
    return sortedAndIndexedReports.filter(r => {
      const reportType = r.type || 'student_note';
      const matchesTab = reportType === activeTab;
      
      const matchesSearch = 
        !keyword ||
        (r.student_name && r.student_name.toLowerCase().includes(keyword)) ||
        (r.teacher_name && r.teacher_name.toLowerCase().includes(keyword)) ||
        (r.content && r.content.toLowerCase().includes(keyword));
      
      const matchesClass = 
        !selectedClassFilter || 
        r.class_id === selectedClassFilter || 
        r.current_class === selectedClassFilter;

      const matchesGrade = 
        !selectedGradeFilter || 
        (r.current_class && r.current_class.startsWith(selectedGradeFilter));

      return matchesTab && matchesSearch && matchesClass && matchesGrade;
    });
  }, [sortedAndIndexedReports, searchTerm, selectedClassFilter, selectedGradeFilter, activeTab]);

  const totalPages = Math.ceil(filteredReports.length / pageSize) || 1;
  const safeCurrentPage = totalPages === 0 ? 1 : Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const paginatedReports = filteredReports.slice(startIndex, startIndex + pageSize);

  const displayStart = filteredReports.length === 0 ? 0 : startIndex + 1;
  const displayEnd = Math.min(startIndex + pageSize, filteredReports.length);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    if (tableTopRef.current) {
      tableTopRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="report-management-page">
      {notification && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-white ${notification.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`} style={{ zIndex: 9999 }}>
          {notification.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* 3 Thẻ thống kê tổng quan */}
      <div className="student-stats-section">
        <h2>Tổng quan Báo cáo & Đóng góp</h2>
        <div className="student-stats-grid">
          <div className="student-stat-card blue">
            <div className="student-stat-icon"><FileText size={22} /></div>
            <div className="student-stat-info">
              <span>Nhận xét học sinh</span>
              <strong>{stats.teacherNotes}</strong>
            </div>
          </div>
          <div className="student-stat-card orange">
            <div className="student-stat-icon"><MessageSquare size={22} /></div>
            <div className="student-stat-info">
              <span>Báo cáo hệ thống</span>
              <strong>{stats.systemIssues}</strong>
            </div>
          </div>
          <div className="student-stat-card purple">
            <div className="student-stat-icon"><HelpCircle size={22} /></div>
            <div className="student-stat-info">
              <span>Ý kiến đóng góp</span>
              <strong>{stats.userFeedbacks}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Panel chính */}
      <div className="student-panel" ref={tableTopRef}>
        <div className="student-panel-heading">
          <div>
            <h2>Quản lý Báo cáo & Ý kiến</h2>
            <p>Theo dõi chi tiết nhận xét học tập, sự cố hệ thống và ý kiến đóng góp</p>
          </div>
        </div>

        {/* Thanh 3 Tabs điều hướng */}
        <div style={{ display: 'flex', gap: '8px', padding: '16px 24px 0 24px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#fff', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('student_note')}
            style={{
              padding: '10px 18px',
              borderRadius: '10px 10px 0 0',
              border: 'none',
              borderBottom: activeTab === 'student_note' ? '3px solid #2563eb' : '3px solid transparent',
              backgroundColor: activeTab === 'student_note' ? '#eff6ff' : 'transparent',
              color: activeTab === 'student_note' ? '#2563eb' : '#64748b',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <FileText size={16} /> Nhận xét học sinh
          </button>

          <button
            onClick={() => setActiveTab('system_issue')}
            style={{
              padding: '10px 18px',
              borderRadius: '10px 10px 0 0',
              border: 'none',
              borderBottom: activeTab === 'system_issue' ? '3px solid #2563eb' : '3px solid transparent',
              backgroundColor: activeTab === 'system_issue' ? '#eff6ff' : 'transparent',
              color: activeTab === 'system_issue' ? '#2563eb' : '#64748b',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <MessageSquare size={16} /> Báo cáo hệ thống
          </button>

          <button
            onClick={() => setActiveTab('user_feedback')}
            style={{
              padding: '10px 18px',
              borderRadius: '10px 10px 0 0',
              border: 'none',
              borderBottom: activeTab === 'user_feedback' ? '3px solid #2563eb' : '3px solid transparent',
              backgroundColor: activeTab === 'user_feedback' ? '#eff6ff' : 'transparent',
              color: activeTab === 'user_feedback' ? '#2563eb' : '#64748b',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <HelpCircle size={16} /> Ý kiến đóng góp
          </button>
        </div>

        {/* Thanh tìm kiếm và bộ lọc */}
        <div className="student-filters" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="student-search-right" style={{ flex: 1, minWidth: '260px', position: 'relative' }}>
            <input 
              type="text" 
              placeholder="Tìm theo tên học sinh, người gửi, nội dung..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '100%', height: '40px', padding: '0 40px 0 16px', borderRadius: '10px', border: '1px solid #dfe7f2', backgroundColor: '#fff', fontSize: '13px', outline: 'none' }}
            />
            <span style={{ position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', display: 'flex', pointerEvents: 'none' }}>
              <Search size={16} />
            </span>
          </div>

          <div style={{ minWidth: '150px' }}>
            <select 
              value={selectedGradeFilter} 
              onChange={(e) => { setSelectedGradeFilter(e.target.value); setSelectedClassFilter(''); }}
              style={{ width: '100%', height: '40px', padding: '0 12px', borderRadius: '10px', border: '1px solid #dfe7f2', backgroundColor: '#fff', fontSize: '13px', color: '#172033', outline: 'none', cursor: 'pointer' }}
            >
              <option value="">Tất cả Khối</option>
              <option value="10">Khối 10</option>
              <option value="11">Khối 11</option>
              <option value="12">Khối 12</option>
            </select>
          </div>

          <div style={{ minWidth: '160px' }}>
            <select 
              value={selectedClassFilter} 
              onChange={(e) => setSelectedClassFilter(e.target.value)}
              style={{ width: '100%', height: '40px', padding: '0 12px', borderRadius: '10px', border: '1px solid #dfe7f2', backgroundColor: '#fff', fontSize: '13px', color: '#172033', outline: 'none', cursor: 'pointer' }}
            >
              <option value="">Tất cả các lớp</option>
              {classList
                .filter(c => !selectedGradeFilter || (c.name && c.name.startsWith(selectedGradeFilter)))
                .map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
            </select>
          </div>

          <button onClick={() => fetchReportsInBackground(false)} className="refresh-button" title="Làm mới">
            <RefreshCw size={15} /> Làm mới
          </button>
        </div>

        {/* Bảng dữ liệu với STT cố định không thay đổi khi tìm kiếm */}
        <div className="student-table-wrap">
          <table className="student-table">
            <thead>
              <tr>
                <th style={{ width: '60px', textAlign: 'center' }}>STT</th>
                <th style={{ width: '18%' }}>Học sinh / Người gửi</th>
                <th style={{ width: '12%' }}>Lớp</th>
                <th style={{ width: '15%' }}>Người ghi nhận</th>
                <th style={{ width: '13%' }}>Môn học / Chủ đề</th>
                <th style={{ width: '30%' }}>Nội dung</th>
                <th style={{ textAlign: 'center', width: '110px' }}>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {loading && reports.length === 0 ? (
                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>Đang tải dữ liệu ngầm...</td></tr>
              ) : paginatedReports.length === 0 ? (
                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Chưa có dữ liệu nào trong mục này</td></tr>
              ) : (
                paginatedReports.map((report) => (
                  <tr key={report.id || report.student_id}>
                    {/* STT cố định theo thứ tự A-Z toàn trường */}
                    <td style={{ textAlign: 'center', fontWeight: 600, color: '#64748b' }}>{report.originalIndex}</td>
                    <td>
                      {/* Bấm vào tên học sinh mở Modal chi tiết y hệt nút Xem */}
                      <span 
                        onClick={() => handleOpenDetail(report)}
                        style={{ fontWeight: 600, color: '#2563eb', cursor: 'pointer' }}
                        title="Bấm để xem chi tiết học sinh"
                      >
                        {report.student_name}
                      </span>
                    </td>
                    <td><span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-semibold">{report.current_class}</span></td>
                    <td>{report.teacher_name}</td>
                    <td><span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-md text-xs font-semibold">{report.subject}</span></td>
                    <td style={{ color: report.has_note === false ? '#94a3b8' : '#334155', fontStyle: report.has_note === false ? 'italic' : 'normal' }}>
                      {report.content}
                    </td>
                    <td>
                      <div className="row-actions" style={{ justifyContent: 'center', display: 'flex', gap: '6px' }}>
                        <button 
                          className="action-btn-view"
                          onClick={() => handleOpenDetail(report)}
                          title="Xem chi tiết"
                        >
                          <Eye size={15} />
                        </button>
                        <button 
                          className="action-btn-delete"
                          onClick={() => handleDeleteReport(report.student_id, report.id)}
                          title="Xóa"
                          disabled={!report.has_note}
                          style={{ opacity: report.has_note ? 1 : 0.4, cursor: report.has_note ? 'pointer' : 'not-allowed' }}
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Thanh phân trang */}
        <div className="class-pagination" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 28px' }}>
          <span>Hiển thị {displayStart}-{displayEnd} trên {filteredReports.length} kết quả</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button 
              disabled={safeCurrentPage === 1} 
              onClick={() => handlePageChange(1)}
              style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#fff', cursor: safeCurrentPage === 1 ? 'not-allowed' : 'pointer' }}
            >
              <ChevronLeft size={16} />
            </button>
            <button 
              disabled={safeCurrentPage === 1} 
              onClick={() => handlePageChange(Math.max(1, safeCurrentPage - 1))}
              style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#fff', cursor: safeCurrentPage === 1 ? 'not-allowed' : 'pointer' }}
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button 
                key={page} 
                onClick={() => handlePageChange(page)}
                style={{ 
                  padding: '6px 12px', 
                  borderRadius: '6px', 
                  border: '1px solid #cbd5e1', 
                  background: safeCurrentPage === page ? '#2563eb' : '#fff', 
                  color: safeCurrentPage === page ? '#fff' : '#334155',
                  fontWeight: '600',
                  cursor: 'pointer' 
                }}
              >
                {page}
              </button>
            ))}
            <button 
              disabled={totalPages === 0 || safeCurrentPage === totalPages} 
              onClick={() => handlePageChange(Math.min(totalPages, safeCurrentPage + 1))}
              style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#fff', cursor: (totalPages === 0 || safeCurrentPage === totalPages) ? 'not-allowed' : 'pointer' }}
            >
              <ChevronRight size={16} />
            </button>
            <button 
              disabled={totalPages === 0 || safeCurrentPage === totalPages} 
              onClick={() => handlePageChange(totalPages)}
              style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', background: '#fff', cursor: (totalPages === 0 || safeCurrentPage === totalPages) ? 'not-allowed' : 'pointer' }}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Modal Chi tiết học sinh theo mẫu ảnh 2 */}
      {showDetailModal && selectedStudentDetail && (
        <div className="student-modal-overlay" style={{ zIndex: 9999 }}>
          <div className="student-modal-container" style={{ maxWidth: '750px', width: '90%', borderRadius: '16px' }} onClick={(e) => e.stopPropagation()}>
            <div className="student-modal-header" style={{ borderBottom: '1px solid #f1f5f9', padding: '20px 24px' }}>
              <div className="student-modal-title-wrap">
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
                  Hồ sơ chi tiết: {selectedStudentDetail.full_name}
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>Xem toàn bộ hồ sơ, lớp học và lịch sử ghi chú của học sinh.</p>
              </div>
              <button onClick={() => setShowDetailModal(false)} className="student-modal-close" title="Đóng"><X size={18} /></button>
            </div>

            <div className="student-modal-form" style={{ padding: '24px', maxHeight: '75vh', overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginBottom: '20px' }}>
                <div className="detail-item" style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Ngày sinh:</span>
                  <strong style={{ fontSize: '14px', color: '#0f172a' }}>{selectedStudentDetail.birthday ? new Date(selectedStudentDetail.birthday).toLocaleDateString('vi-VN') : '---'}</strong>
                </div>
                <div className="detail-item" style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Giới tính:</span>
                  <strong style={{ fontSize: '14px', color: '#0f172a' }}>{selectedStudentDetail.gender || '---'}</strong>
                </div>
                <div className="detail-item" style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '2px' }}>Lớp hiện tại:</span>
                  <strong style={{ fontSize: '14px', color: '#2563eb' }}>{selectedStudentDetail.current_class || 'Chưa phân lớp'}</strong>
                </div>
                <div className="detail-item" style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '2px' }}>SĐT Phụ huynh:</span>
                  <strong style={{ fontSize: '14px', color: '#0f172a' }}>{selectedStudentDetail.phone_number || selectedStudentDetail.parent_phonenumber || '---'}</strong>
                </div>
              </div>

              <div className="form-group" style={{ marginTop: '20px' }}>
                <label style={{ fontWeight: '700', color: '#1e293b', marginBottom: '10px', display: 'block', fontSize: '15px' }}>
                  Lịch sử báo cáo & Ghi chú tiết học:
                </label>
                <div className="detail-notes-box" style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px', background: '#f8fafc' }}>
                  {selectedStudentDetail.notes && selectedStudentDetail.notes.length > 0 ? (
                    selectedStudentDetail.notes.map((n, idx) => (
                      <div key={idx} className="report-item" style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>
                          <div>
                            <span style={{ fontWeight: '600', color: '#2563eb', marginRight: '12px' }}>Giáo viên: {n.teacher_name || 'Chưa rõ'}</span>
                            <span style={{ fontWeight: '500', color: '#475569', marginRight: '12px' }}>Môn: {n.subject || '---'}</span>
                            <span>{n.created_at ? new Date(n.created_at).toLocaleString('vi-VN') : ''}</span>
                          </div>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button type="button" onClick={() => showNotify('Đã lưu trữ')} title="Lưu trữ" style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', color: '#475569', fontSize: '11px', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Archive size={12} /> Lưu trữ
                            </button>
                            <button type="button" onClick={() => handleDeleteReport(selectedStudentDetail.id, n.id)} title="Xóa" style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', color: '#dc2626', fontSize: '11px', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Trash2 size={12} /> Xóa
                            </button>
                          </div>
                        </div>
                        <p style={{ margin: 0, fontSize: '13px', color: '#334155', lineHeight: '1.5' }}>{n.content || 'Không có nội dung'}</p>
                      </div>
                    ))
                  ) : (
                    <p style={{ textAlign: 'center', color: '#64748b', fontSize: '13px', margin: '15px 0' }}>Chưa có ghi chú hoặc báo cáo nào cho học sinh này.</p>
                  )}
                </div>
              </div>

              <div className="student-modal-actions" style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={() => setShowDetailModal(false)} className="primary-button" style={{ height: '38px', padding: '0 20px', borderRadius: '8px' }}>Đóng</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}