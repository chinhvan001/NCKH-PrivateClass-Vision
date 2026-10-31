import React, { useState, useEffect, useRef } from 'react';
import { 
  Users, UserCheck, UserX, Clock, Search, RefreshCw, 
  Plus, Eye, Edit, Trash2, X, CheckCircle, AlertCircle, ChevronLeft, ChevronRight, Archive 
} from 'lucide-react';

import { getAuthHeaders } from '../../../utils/AuthSession';

export default function StudentManagementPanel() {
  const [students, setStudents] = useState([]);
  const [classList, setClassList] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, paused: 0, dropped: 0 });
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Bộ lọc Khối (mặc định '12'), Lớp và Trạng thái
  const [selectedGradeFilter, setSelectedGradeFilter] = useState('12');
  const [selectedClassFilter, setSelectedClassFilter] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('');

  // Phân trang 20 học sinh / trang
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Ref để scroll lên đầu bảng khi chuyển trang
  const tableTopRef = useRef(null);
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);

  const [formData, setFormData] = useState({
    full_name: '',
    birthday: '',
    gender: 'Nam',
    parent_phonenumber: '',
    parent_name: '',
    class_id: '',
    status: 'Đang học'
  });

  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchStudents(false);
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedGradeFilter, selectedClassFilter, selectedStatusFilter, searchTerm]);

  const fetchStudents = async (forceRefresh = false) => {
    const cacheKey = 'app_students_cache_data';
    const cacheTimeKey = 'app_students_cache_time';
    const now = new Date().getTime();
    
    if (!forceRefresh) {
      const cachedData = sessionStorage.getItem(cacheKey);
      const cachedTime = sessionStorage.getItem(cacheTimeKey);
      if (cachedData && cachedTime && (now - parseInt(cachedTime) < 180000)) {
        try {
          const parsed = JSON.parse(cachedData);
          setStudents(parsed.data);
          setStats(parsed.stats);
          setClassList(parsed.classes || []);
          return;
        } catch (e) {
          // Bỏ qua lỗi parse
        }
      }
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/students', { headers: await getAuthHeaders() });
      const result = await response.json();
      if (result.success) {
        setStudents(result.data);
        setStats(result.stats);
        setClassList(result.classes || []);

        sessionStorage.setItem(cacheKey, JSON.stringify(result));
        sessionStorage.setItem(cacheTimeKey, now.toString());
      }
    } catch (error) {
      showNotify('Lỗi khi tải danh sách học sinh', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotify = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const formatDate = (birthdayField) => {
    if (!birthdayField) return '---';
    try {
      let date;
      if (typeof birthdayField === 'object' && birthdayField._seconds) {
        date = new Date(birthdayField._seconds * 1000);
      } else {
        date = new Date(birthdayField);
      }
      if (isNaN(date.getTime())) return birthdayField;
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}/${month}/${year}`;
    } catch (error) {
      return birthdayField;
    }
  };

  const getBirthdayForInput = (birthdayField) => {
    if (!birthdayField) return '';
    try {
      let date;
      if (typeof birthdayField === 'object' && birthdayField._seconds) {
        date = new Date(birthdayField._seconds * 1000);
      } else {
        date = new Date(birthdayField);
      }
      if (isNaN(date.getTime())) return '';
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    } catch (error) {
      return '';
    }
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/v1/students', {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify(formData)
      });
      const result = await res.json();
      if (result.success) {
        showNotify('Thêm học sinh thành công!');
        setShowAddModal(false);
        sessionStorage.removeItem('app_students_cache_data');
        fetchStudents(true);
        setFormData({ full_name: '', birthday: '', gender: 'Nam', parent_phonenumber: '', parent_name: '', class_id: '', status: 'Đang học' });
      } else {
        showNotify(result.error || 'Thêm thất bại', 'error');
      }
    } catch (err) {
      showNotify('Lỗi kết nối server', 'error');
    }
  };

  const handleUpdateStudent = async (e) => {
    e.preventDefault();
    if (!selectedStudent) return;
    try {
      const res = await fetch(`/api/v1/students/${selectedStudent.id}`, {
        method: 'PUT',
        headers: await getAuthHeaders(),
        body: JSON.stringify(formData)
      });
      const result = await res.json();
      if (result.success) {
        showNotify('Cập nhật thông tin học sinh thành công!');
        setShowEditModal(false);
        sessionStorage.removeItem('app_students_cache_data');
        fetchStudents(true);
      } else {
        showNotify(result.error || 'Cập nhật thất bại', 'error');
      }
    } catch (err) {
      showNotify('Lỗi kết nối server', 'error');
    }
  };

  const handleDelete = async (studentId) => {
    if (!window.confirm('Bạn có chắc chắn muốn chuyển trạng thái học sinh này thành thôi học?')) return;
    try {
      const res = await fetch(`/api/v1/students/${studentId}`, { method: 'DELETE', headers: await getAuthHeaders() });
      const result = await res.json();
      if (result.success) {
        showNotify('Đã cập nhật trạng thái học sinh');
        sessionStorage.removeItem('app_students_cache_data');
        fetchStudents(true);
      } else {
        showNotify(result.error, 'error');
      }
    } catch (err) {
      showNotify('Lỗi xóa học sinh', 'error');
    }
  };

  const handleOpenDetail = async (student) => {
    try {
      const res = await fetch(`/api/v1/students/${student.id}`, { headers: await getAuthHeaders() });
      const result = await res.json();
      let detailData = result.success ? result.data : student;
      if (detailData.gender === 'female' || detailData.gender === 'Female') detailData.gender = 'Nữ';
      else if (detailData.gender === 'male' || detailData.gender === 'Male') detailData.gender = 'Nam';
      setSelectedStudent(detailData);
      setShowDetailModal(true);
    } catch (error) {
      setSelectedStudent(student);
      setShowDetailModal(true);
    }
  };

  const handleDeleteReport = (reportIdx) => {
    if (!window.confirm('Bạn có chắc muốn xóa báo cáo này?')) return;
    const updatedNotes = [...(selectedStudent.notes || [
      { teacher_name: 'Nguyễn Văn A', created_at: '14:30 - 27/10/2026', content: 'Học sinh tập trung tốt trong giờ học toán, hoàn thành đầy đủ bài tập về nhà.' },
      { teacher_name: 'Trần Thị B', created_at: '09:15 - 24/10/2026', content: 'Đi học muộn 10 phút, cần nhắc nhở tác phong.' }
    ])];
    updatedNotes.splice(reportIdx, 1);
    setSelectedStudent({ ...selectedStudent, notes: updatedNotes });
    showNotify('Đã xóa báo cáo thành công');
  };

  const handleArchiveReport = (reportIdx) => {
    showNotify('Đã lưu trữ báo cáo thành công');
  };

  // Lọc theo Khối, Lớp, Trạng thái, Từ khóa tìm kiếm và Sắp xếp A-B-C
  const filteredStudents = students.filter(s => {
    const matchesSearch = 
      s.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.phone_number && s.phone_number.includes(searchTerm));
    
    const matchesClass = 
      !selectedClassFilter || 
      s.class_id === selectedClassFilter || 
      s.current_class === selectedClassFilter;

    const matchesGrade = 
      !selectedGradeFilter || 
      (s.current_class && s.current_class.startsWith(selectedGradeFilter)) ||
      (s.grade && String(s.grade) === selectedGradeFilter);

    const matchesStatus = 
      !selectedStatusFilter || 
      s.status === selectedStatusFilter;

    return matchesSearch && matchesClass && matchesGrade && matchesStatus;
  }).sort((a, b) => (a.full_name || '').localeCompare(b.full_name || '', 'vi', { sensitivity: 'base' }));

  // Phân trang
  const totalPages = Math.ceil(filteredStudents.length / pageSize) || 1;
  const paginatedStudents = filteredStudents.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    if (tableTopRef.current) {
      tableTopRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="student-management-page">
      {notification && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-white ${notification.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`}>
          {notification.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Thống kê tổng quan */}
      <div className="student-stats-section">
        <h2>Tổng quan học sinh</h2>
        <div className="student-stats-grid">
          <div className="student-stat-card blue">
            <div className="student-stat-icon"><Users size={22} /></div>
            <div className="student-stat-info">
              <span>Tổng số học sinh</span>
              <strong>{stats.total}</strong>
            </div>
          </div>
          <div className="student-stat-card green">
            <div className="student-stat-icon"><UserCheck size={22} /></div>
            <div className="student-stat-info">
              <span>Đang học</span>
              <strong>{stats.active}</strong>
            </div>
          </div>
          <div className="student-stat-card orange">
            <div className="student-stat-icon"><Clock size={22} /></div>
            <div className="student-stat-info">
              <span>Tạm nghỉ</span>
              <strong>{stats.paused}</strong>
            </div>
          </div>
          <div className="student-stat-card red">
            <div className="student-stat-icon"><UserX size={22} /></div>
            <div className="student-stat-info">
              <span>Đã thôi học</span>
              <strong>{stats.dropped}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Panel chính */}
      <div className="student-panel" ref={tableTopRef}>
        <div className="student-panel-heading">
          <div>
            <h2>Danh sách học sinh toàn trường</h2>
            <p>Quản lý hồ sơ, thông tin liên lạc và trạng thái học tập của học sinh</p>
          </div>
          <button 
            onClick={() => {
              setFormData({ full_name: '', birthday: '', gender: 'Nam', parent_phonenumber: '', parent_name: '', class_id: '', status: 'Đang học' });
              setShowAddModal(true);
            }}
            className="primary-button"
          >
            <Plus size={16} /> Thêm học sinh
          </button>
        </div>

        {/* Thanh tìm kiếm và bộ lọc Khối, Lớp, Trạng thái */}
        <div className="student-filters" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="student-search" style={{ flex: 1, minWidth: '200px' }}>
            <input 
              type="text" 
              placeholder="Tìm kiếm theo tên, số điện thoại..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <span className="student-search-icon"><Search size={16} /></span>
          </div>

          {/* Bộ lọc Khối */}
          <div style={{ minWidth: '160px' }}>
            <select 
              value={selectedGradeFilter} 
              onChange={(e) => {
                setSelectedGradeFilter(e.target.value);
                setSelectedClassFilter(''); 
              }}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '14px', color: '#1e293b', fontWeight: '500', outline: 'none', cursor: 'pointer' }}
            >
              <option value="" style={{ fontWeight: '600', color: '#2563eb', backgroundColor: '#f1f5f9' }}>Tất cả các khối</option>
              <option disabled style={{ fontSize: '4px', backgroundColor: '#e2e8f0' }}>──────────</option>
              <option value="10">Khối 10</option>
              <option value="11">Khối 11</option>
              <option value="12">Khối 12</option>
            </select>
          </div>

          {/* Bộ lọc Lớp */}
          <div style={{ minWidth: '160px' }}>
            <select 
              value={selectedClassFilter} 
              onChange={(e) => setSelectedClassFilter(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '14px', color: '#1e293b', fontWeight: '500', outline: 'none', cursor: 'pointer' }}
            >
              <option value="" style={{ fontWeight: '600', color: '#2563eb', backgroundColor: '#f1f5f9' }}>Tất cả các lớp</option>
              <option disabled style={{ fontSize: '4px', backgroundColor: '#e2e8f0' }}>──────────</option>
              {classList
                .filter(c => !selectedGradeFilter || (c.name && c.name.startsWith(selectedGradeFilter)))
                .map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
            </select>
          </div>

          {/* Bộ lọc Trạng thái học sinh */}
          <div style={{ minWidth: '160px' }}>
            <select 
              value={selectedStatusFilter} 
              onChange={(e) => setSelectedStatusFilter(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '14px', color: '#1e293b', fontWeight: '500', outline: 'none', cursor: 'pointer' }}
            >
              <option value="" style={{ fontWeight: '600', color: '#2563eb', backgroundColor: '#f1f5f9' }}>Tất cả trạng thái</option>
              <option disabled style={{ fontSize: '4px', backgroundColor: '#e2e8f0' }}>──────────</option>
              <option value="Đang học">Đang học</option>
              <option value="Tạm nghỉ">Tạm nghỉ</option>
              <option value="Đã thôi học">Đã thôi học</option>
            </select>
          </div>

          <button onClick={() => {
            sessionStorage.removeItem('app_students_cache_data');
            fetchStudents(true);
          }} className="refresh-button" title="Làm mới">
            <RefreshCw size={15} /> Làm mới
          </button>
        </div>

        {/* Bảng dữ liệu học sinh */}
        <div className="student-table-wrap">
          <table className="student-table">
            <thead>
              <tr>
                <th style={{ width: '60px', textAlign: 'center' }}>STT</th>
                <th style={{ width: '22%' }}>Họ và tên</th>
                <th style={{ width: '13%' }}>Ngày sinh</th>
                <th style={{ width: '10%' }}>Giới tính</th>
                <th style={{ width: '12%' }}>Lớp hiện tại</th>
                <th style={{ width: '13%' }}>Trạng thái</th>
                <th style={{ width: '16%' }}>Số điện thoại</th>
                <th style={{ width: '14%' }}>Phụ huynh</th>
                <th style={{ textAlign: 'center', width: '110px' }}>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="9" style={{ textAlign: 'center', padding: '40px' }}>Đang tải dữ liệu học sinh...</td></tr>
              ) : paginatedStudents.length === 0 ? (
                <tr><td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Không tìm thấy học sinh nào trong cơ sở dữ liệu</td></tr>
              ) : (
                paginatedStudents.map((student, index) => {
                  const stt = (currentPage - 1) * pageSize + index + 1;
                  return (
                    <tr
                      key={student.id || index}
                      title="Nhấn đúp để xem thông tin"
                      onDoubleClick={(e) => {
                        if (!e.target.closest('button')) handleOpenDetail(student); // nhấn đúp vào nút thì nút xử lý
                      }}
                    >
                      <td style={{ textAlign: 'center', fontWeight: 600, color: '#64748b' }}>{stt}</td>
                      <td>
                        <span 
                          onClick={() => handleOpenDetail(student)}
                          style={{ fontWeight: 600, color: '#2563eb', cursor: 'pointer' }}
                          title="Bấm để xem chi tiết"
                        >
                          {student.full_name}
                        </span>
                      </td>
                      <td>{formatDate(student.birthday)}</td>
                      <td>{student.gender}</td>
                      <td><span className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-semibold">{student.current_class}</span></td>
                      <td>
                        <span className={`student-status ${
                          student.status === 'Đang học' ? 'active' :
                          student.status === 'Tạm nghỉ' ? 'paused' : 'inactive'
                        }`}>
                          {student.status}
                        </span>
                      </td>
                      <td>{student.phone_number || '---'}</td>
                      <td>{student.parent_name || '---'}</td>
                      <td>
                        {/* Cập nhật các nút thao tác danh sách chính có hiệu ứng hover đổi màu nền nổi bật */}
                        <div className="row-actions" style={{ justifyContent: 'center', display: 'flex', gap: '6px' }}>
                          <button 
                            onClick={() => handleOpenDetail(student)} 
                            title="Xem chi tiết"
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              backgroundColor: '#fff',
                              color: '#2563eb',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#eff6ff'; e.currentTarget.style.borderColor = '#2563eb'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fff'; e.currentTarget.style.borderColor = '#cbd5e1'; }}
                          >
                            <Eye size={15} />
                          </button>
                          <button 
                            onClick={() => {
                              setSelectedStudent(student);
                              setFormData({
                                full_name: student.full_name || '',
                                birthday: getBirthdayForInput(student.birthday),
                                gender: student.gender === 'female' || student.gender === 'Female' || student.gender === 'Nữ' ? 'Nữ' : 'Nam',
                                parent_phonenumber: student.phone_number || '',
                                parent_name: student.parent_name || '',
                                class_id: student.class_id || '',
                                status: student.status || 'Đang học'
                              });
                              setShowEditModal(true);
                            }} 
                            title="Chỉnh sửa"
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              border: '1px solid #cbd5e1',
                              backgroundColor: '#fff',
                              color: '#475569',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.borderColor = '#475569'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fff'; e.currentTarget.style.borderColor = '#cbd5e1'; }}
                          >
                            <Edit size={15} />
                          </button>
                          <button 
                            onClick={() => handleDelete(student.id)} 
                            title="Xóa/Thôi học" 
                            style={{
                              padding: '6px',
                              borderRadius: '6px',
                              border: '1px solid #fecaca',
                              backgroundColor: '#fff',
                              color: '#dc2626',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; e.currentTarget.style.borderColor = '#dc2626'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fff'; e.currentTarget.style.borderColor = '#fecaca'; }}
                          >
                            <Trash2 size={15} />
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

        {/* Thanh phân trang */}
        <div className="class-pagination" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 28px' }}>
          <span>Hiển thị {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, filteredStudents.length)} trong tổng số {filteredStudents.length} học sinh</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button 
              disabled={currentPage === 1} 
              onClick={() => handlePageChange(currentPage - 1)}
              title="Trang trước"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button 
                key={page} 
                className={currentPage === page ? 'current-page' : ''}
                onClick={() => handlePageChange(page)}
              >
                {page}
              </button>
            ))}
            <button 
              disabled={currentPage === totalPages} 
              onClick={() => handlePageChange(currentPage + 1)}
              title="Trang sau"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Modal Thêm học sinh mới */}
      {showAddModal && (
        <div className="student-modal-overlay">
          <div className="student-modal-container">
            <div className="student-modal-header">
              <div className="student-modal-title-wrap">
                <h3>Thêm học sinh mới</h3>
                <p>Tạo hồ sơ học sinh mới trong hệ thống quản lý.</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="student-modal-close" title="Đóng">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateStudent} className="student-modal-form">
              <div className="form-group">
                <label>Họ và tên *</label>
                <input 
                  type="text" required 
                  value={formData.full_name} 
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  placeholder="Nhập họ và tên học sinh"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Ngày sinh</label>
                  <input 
                    type="date" 
                    value={formData.birthday} 
                    onChange={(e) => setFormData({...formData, birthday: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Giới tính</label>
                  <select 
                    value={formData.gender} 
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                  >
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Gán vào lớp</label>
                  <select 
                    value={formData.class_id} 
                    onChange={(e) => setFormData({...formData, class_id: e.target.value})}
                  >
                    <option value="">-- Chưa phân lớp --</option>
                    {classList.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Trạng thái</label>
                  <select 
                    value={formData.status} 
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                  >
                    <option value="Đang học">Đang học</option>
                    <option value="Tạm nghỉ">Tạm nghỉ</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Số điện thoại phụ huynh</label>
                <input 
                  type="text" 
                  value={formData.parent_phonenumber} 
                  onChange={(e) => setFormData({...formData, parent_phonenumber: e.target.value})}
                  placeholder="Nhập số điện thoại"
                />
              </div>
              <div className="student-modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)} className="secondary-button">Hủy</button>
                <button type="submit" className="primary-button">Thêm học sinh</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Chỉnh sửa thông tin học sinh */}
      {showEditModal && (
        <div className="student-modal-overlay">
          <div className="student-modal-container">
            <div className="student-modal-header">
              <div className="student-modal-title-wrap">
                <h3>Chỉnh sửa thông tin học sinh</h3>
                <p>Cập nhật hồ sơ và thông tin liên lạc của học sinh.</p>
              </div>
              <button onClick={() => setShowEditModal(false)} className="student-modal-close" title="Đóng">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleUpdateStudent} className="student-modal-form">
              <div className="form-group">
                <label>Họ và tên *</label>
                <input 
                  type="text" required 
                  value={formData.full_name} 
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Ngày sinh</label>
                  <input 
                    type="date" 
                    value={formData.birthday} 
                    onChange={(e) => setFormData({...formData, birthday: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Giới tính</label>
                  <select 
                    value={formData.gender} 
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                  >
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Lớp học</label>
                  <select 
                    value={formData.class_id} 
                    onChange={(e) => setFormData({...formData, class_id: e.target.value})}
                  >
                    <option value="">-- Chưa phân lớp --</option>
                    {classList.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Trạng thái</label>
                  <select 
                    value={formData.status} 
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                  >
                    <option value="Đang học">Đang học</option>
                    <option value="Tạm nghỉ">Tạm nghỉ</option>
                    <option value="Đã thôi học">Đã thôi học</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Số điện thoại phụ huynh</label>
                <input 
                  type="text" 
                  value={formData.parent_phonenumber} 
                  onChange={(e) => setFormData({...formData, parent_phonenumber: e.target.value})}
                />
              </div>
              <div className="student-modal-actions">
                <button type="button" onClick={() => setShowEditModal(false)} className="secondary-button">Hủy</button>
                <button type="submit" className="primary-button">Cập nhật</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Thông tin chi tiết học sinh */}
      {showDetailModal && selectedStudent && (
        <div className="student-modal-overlay">
          <div className="student-modal-container" style={{ maxWidth: '750px', width: '90%' }}>
            <div className="student-modal-header">
              <div className="student-modal-title-wrap">
                <h3>Thông tin chi tiết học sinh</h3>
                <p>Xem toàn bộ hồ sơ, lớp học và lịch sử báo cáo của học sinh.</p>
              </div>
              <button onClick={() => setShowDetailModal(false)} className="student-modal-close" title="Đóng">
                <X size={18} />
              </button>
            </div>
            <div className="student-modal-form">
              <div className="detail-item"><span>Họ và tên:</span><strong>{selectedStudent.full_name}</strong></div>
              <div className="detail-item"><span>Ngày sinh:</span><strong>{formatDate(selectedStudent.birthday)}</strong></div>
              <div className="detail-item"><span>Giới tính:</span><strong>{selectedStudent.gender}</strong></div>
              <div className="detail-item"><span>Lớp hiện tại:</span><strong className="text-blue-600">{selectedStudent.current_class}</strong></div>
              <div className="detail-item"><span>SĐT Phụ huynh:</span><strong>{selectedStudent.parent_phonenumber || selectedStudent.phone_number || '---'}</strong></div>
              <div className="detail-item"><span>Trạng thái:</span><strong className="text-green-600">{selectedStudent.status}</strong></div>
              
              <div className="form-group" style={{ marginTop: '16px' }}>
                <label style={{ fontWeight: '700', color: '#1e293b', marginBottom: '8px', display: 'block' }}>Lịch sử báo cáo & Ghi chú:</label>
                <div className="detail-notes-box" style={{ maxHeight: '280px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', background: '#f8fafc' }}>
                  {selectedStudent.notes && selectedStudent.notes.length > 0 ? (
                    selectedStudent.notes.map((n, idx) => (
                      <div key={idx} className="report-item" style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0', position: 'relative' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          <div>
                            <span style={{ fontWeight: '600', color: '#2563eb', marginRight: '10px' }}>GV: {n.teacher_name || n.teacher || 'Chưa rõ giáo viên'}</span>
                            <span>{n.created_at || n.time || '---'}</span>
                          </div>
                          {/* Nút Lưu trữ và Xóa báo cáo có hiệu ứng hover đổi màu nền nổi bật */}
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button 
                              type="button" 
                              onClick={() => handleArchiveReport(idx)}
                              title="Lưu trữ báo cáo"
                              style={{ 
                                background: '#f1f5f9', 
                                border: '1px solid #cbd5e1', 
                                borderRadius: '6px', 
                                padding: '5px 8px', 
                                cursor: 'pointer', 
                                color: '#475569', 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '4px', 
                                fontSize: '11px',
                                fontWeight: '500',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#e2e8f0'; e.currentTarget.style.color = '#1e293b'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.color = '#475569'; }}
                            >
                              <Archive size={12} /> Lưu trữ
                            </button>
                            <button 
                              type="button" 
                              onClick={() => handleDeleteReport(idx)}
                              title="Xóa báo cáo"
                              style={{ 
                                background: '#fef2f2', 
                                border: '1px solid #fecaca', 
                                borderRadius: '6px', 
                                padding: '5px 8px', 
                                cursor: 'pointer', 
                                color: '#dc2626', 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '4px', 
                                fontSize: '11px',
                                fontWeight: '500',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fee2e2'; e.currentTarget.style.borderColor = '#f87171'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; e.currentTarget.style.borderColor = '#fecaca'; }}
                            >
                              <Trash2 size={12} /> Xóa
                            </button>
                          </div>
                        </div>
                        <p style={{ margin: 0, fontSize: '13px', color: '#334155', paddingRight: '10px' }}>{n.content || n.message}</p>
                      </div>
                    ))
                  ) : (
                    <div>
                      <div className="report-item" style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          <div>
                            <span style={{ fontWeight: '600', color: '#2563eb', marginRight: '10px' }}>GV: Nguyễn Văn A</span>
                            <span>14:30 - 27/10/2026</span>
                          </div>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button 
                              type="button" 
                              onClick={() => handleArchiveReport(0)} 
                              title="Lưu trữ" 
                              style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '5px 8px', cursor: 'pointer', color: '#475569', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: '500', transition: 'all 0.2s ease' }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#e2e8f0'; e.currentTarget.style.color = '#1e293b'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.color = '#475569'; }}
                            >
                              <Archive size={12} /> Lưu trữ
                            </button>
                            <button 
                              type="button" 
                              onClick={() => handleDeleteReport(0)} 
                              title="Xóa" 
                              style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '5px 8px', cursor: 'pointer', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: '500', transition: 'all 0.2s ease' }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fee2e2'; e.currentTarget.style.borderColor = '#f87171'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; e.currentTarget.style.borderColor = '#fecaca'; }}
                            >
                              <Trash2 size={12} /> Xóa
                            </button>
                          </div>
                        </div>
                        <p style={{ margin: 0, fontSize: '13px', color: '#334155' }}>Học sinh tập trung tốt trong giờ học toán, hoàn thành đầy đủ bài tập về nhà.</p>
                      </div>
                      <div className="report-item">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                          <div>
                            <span style={{ fontWeight: '600', color: '#2563eb', marginRight: '10px' }}>GV: Trần Thị B</span>
                            <span>09:15 - 24/10/2026</span>
                          </div>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button 
                              type="button" 
                              onClick={() => handleArchiveReport(1)} 
                              title="Lưu trữ" 
                              style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', padding: '5px 8px', cursor: 'pointer', color: '#475569', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: '500', transition: 'all 0.2s ease' }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#e2e8f0'; e.currentTarget.style.color = '#1e293b'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.color = '#475569'; }}
                            >
                              <Archive size={12} /> Lưu trữ
                            </button>
                            <button 
                              type="button" 
                              onClick={() => handleDeleteReport(1)} 
                              title="Xóa" 
                              style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '5px 8px', cursor: 'pointer', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: '500', transition: 'all 0.2s ease' }}
                              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#fee2e2'; e.currentTarget.style.borderColor = '#f87171'; }}
                              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#fef2f2'; e.currentTarget.style.borderColor = '#fecaca'; }}
                            >
                              <Trash2 size={12} /> Xóa
                            </button>
                          </div>
                        </div>
                        <p style={{ margin: 0, fontSize: '13px', color: '#334155' }}>Đi học muộn 10 phút, cần nhắc nhở tác phong.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="student-modal-actions" style={{ marginTop: '16px' }}>
                <button onClick={() => setShowDetailModal(false)} className="primary-button">Đóng</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}