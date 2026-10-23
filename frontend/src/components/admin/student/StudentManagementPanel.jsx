import React, { useState, useEffect } from 'react';
import { 
  Users, UserCheck, UserX, Clock, Search, RefreshCw, 
  Plus, Eye, Edit, Trash2, X, CheckCircle, AlertCircle
} from 'lucide-react';

import { getAuthHeaders } from '../../../utils/AuthSession';

export default function StudentManagementPanel() {
  const [students, setStudents] = useState([]);
  const [classList, setClassList] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, paused: 0, dropped: 0 });
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 1. Thêm state lưu lớp đang chọn để lọc
  const [selectedClassFilter, setSelectedClassFilter] = useState('');
  
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
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/students', { headers: await getAuthHeaders() });
      const result = await response.json();
      if (result.success) {
        setStudents(result.data);
        setStats(result.stats);
        setClassList(result.classes || []);
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
        fetchStudents();
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
        fetchStudents();
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
        fetchStudents();
      } else {
        showNotify(result.error, 'error');
      }
    } catch (err) {
      showNotify('Lỗi xóa học sinh', 'error');
    }
  };

  // 3. Cập nhật hàm lọc học sinh theo từ khóa và lớp học
  const filteredStudents = students.filter(s => {
    const matchesSearch = 
      s.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.phone_number && s.phone_number.includes(searchTerm));
    
    // Kiểm tra khớp với class_id hoặc tên lớp (tùy thuộc cấu trúc dữ liệu trả về từ API)
    const matchesClass = 
      !selectedClassFilter || 
      s.class_id === selectedClassFilter || 
      s.current_class === selectedClassFilter;

    return matchesSearch && matchesClass;
  });

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
      <div className="student-panel">
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

        {/* Thanh tìm kiếm và bộ lọc lớp */}
        <div className="student-filters" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="student-search" style={{ flex: 1, minWidth: '240px' }}>
            <input 
              type="text" 
              placeholder="Tìm kiếm theo tên, số điện thoại..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <span className="student-search-icon"><Search size={16} /></span>
          </div>

          {/* 2. Thêm thẻ select chọn lớp lọc */}
          <div className="student-class-filter" style={{ minWidth: '180px' }}>
            <select 
              value={selectedClassFilter} 
              onChange={(e) => setSelectedClassFilter(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#fff', fontSize: '14px' }}
            >
              <option value="">Tất cả các lớp</option>
              {classList.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <button onClick={fetchStudents} className="refresh-button" title="Làm mới">
            <RefreshCw size={15} /> Làm mới
          </button>
        </div>

        {/* Bảng dữ liệu */}
        <div className="student-table-wrap">
          <table className="student-table">
            <thead>
              <tr>
                <th>Họ và tên</th>
                <th>Ngày sinh</th>
                <th>Giới tính</th>
                <th>Lớp hiện tại</th>
                <th>Trạng thái</th>
                <th>Số điện thoại</th>
                <th>Phụ huynh</th>
                <th style={{ textAlign: 'center', width: '130px' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>Đang tải dữ liệu học sinh...</td></tr>
              ) : filteredStudents.length === 0 ? (
                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Không tìm thấy học sinh nào trong cơ sở dữ liệu</td></tr>
              ) : (
                filteredStudents.map((student) => (
                  <tr key={student.id}>
                    <td style={{ fontWeight: 600, color: '#1e293b' }}>{student.full_name}</td>
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
                    <td>{student.parent_name}</td>
                    <td>
                      <div className="row-actions" style={{ justifyContent: 'center' }}>
                        <button onClick={async () => {
                          const res = await fetch(`/api/v1/students/${student.id}`, { headers: await getAuthHeaders() });
                          const result = await res.json();
                          if (result.success) {
                            const detailData = result.data;
                            if (detailData.gender === 'female' || detailData.gender === 'Female') detailData.gender = 'Nữ';
                            else if (detailData.gender === 'male' || detailData.gender === 'Male') detailData.gender = 'Nam';
                            setSelectedStudent(detailData);
                          }
                          setShowDetailModal(true);
                        }} title="Xem chi tiết">
                          <Eye size={15} />
                        </button>
                        <button onClick={() => {
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
                        }} title="Chỉnh sửa">
                          <Edit size={15} />
                        </button>
                        <button onClick={() => handleDelete(student.id)} title="Xóa/Thôi học" style={{ color: '#dc2626' }}>
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
          <div className="student-modal-container">
            <div className="student-modal-header">
              <div className="student-modal-title-wrap">
                <h3>Thông tin chi tiết học sinh</h3>
                <p>Xem toàn bộ hồ sơ, lớp học và ghi chú của học sinh.</p>
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
              
              <div className="form-group" style={{ marginTop: '10px' }}>
                <label>Ghi chú / Lịch sử:</label>
                <div className="detail-notes-box">
                  {selectedStudent.notes && selectedStudent.notes.length > 0 ? (
                    selectedStudent.notes.map((n, idx) => (
                      <div key={idx} className="note-row">
                        <p>{n.content}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 italic">Không có ghi chú nào</p>
                  )}
                </div>
              </div>
              <div className="student-modal-actions">
                <button onClick={() => setShowDetailModal(false)} className="primary-button">Đóng</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}