import React, { useState, useEffect } from 'react';
import { 
  Users, Calendar, Clock, Search, RefreshCw, 
  Plus, Eye, Edit, Trash2, X, CheckCircle, AlertCircle 
} from 'lucide-react';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

import { getAuthHeaders } from '../../../utils/AuthSession';
import SessionMonitorModal, { SessionStatusBadge } from './SessionMonitorModal';

export default function SessionDetailPanel() {
  const [sessions, setSessions] = useState([]);
  const [classList, setClassList] = useState([]);
  const [teacherList, setTeacherList] = useState([]);
  const [roomList, setRoomList] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]); 
  const [selectedShift, setSelectedShift] = useState('morning'); // 'morning' | 'afternoon'
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [monitorSession, setMonitorSession] = useState(null); // tiết đang mở bảng giám sát

  const periodsConfigMap = {
    morning: {
      1: { start: '07:00', end: '07:45' },
      2: { start: '07:55', end: '08:40' },
      3: { start: '08:50', end: '09:35' },
      4: { start: '09:45', end: '10:30' },
      5: { start: '10:40', end: '11:25' },
    },
    afternoon: {
      1: { start: '13:00', end: '13:45' },
      2: { start: '13:55', end: '14:40' },
      3: { start: '14:50', end: '15:35' },
      4: { start: '15:45', end: '16:30' },
      5: { start: '16:40', end: '17:25' },
    }
  };

  const [formData, setFormData] = useState({
    class_id: '',
    teacher_id: '',
    subject: '',
    session_date: new Date().toISOString().split('T')[0],
    morning_or_afternoon: 'morning',
    period: 1,
    start_time: '07:00',
    end_time: '07:45',
    room: ''
  });

  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const auth = getAuth();
    const unsubscribe = onAuthStateChanged(auth, () => {
      fetchDataReal();
    });
    return () => unsubscribe();
  }, []);

  const fetchDataReal = async () => {
    setLoading(true);
    try {
      const headers = await getAuthHeaders();

      const [scheduleRes, classRes, teacherRes, roomRes] = await Promise.all([
        fetch('/api/admin/schedules', { headers }),
        fetch('/api/admin/classes', { headers }),
        fetch('/api/admin/teachers', { headers }),
        fetch('/api/admin/rooms', { headers })
      ]);

      const scheduleResult = await scheduleRes.json();
      const classResult = await classRes.json();
      const teacherResult = await teacherRes.json();
      const roomResult = await roomRes.json();

      if (scheduleResult.success) {
        setSessions(scheduleResult.data || []);
      } else {
        showNotify(scheduleResult.message || 'Không thể lấy dữ liệu lịch học', 'error');
      }

      if (classResult.success) {
        setClassList(classResult.data || []);
      } else {
        showNotify(classResult.message || 'Không thể lấy danh sách lớp học', 'error');
      }

      if (teacherResult.success) {
        setTeacherList(teacherResult.data || []);
      }

      if (roomResult.success) {
        setRoomList(roomResult.data || []);
      }
    } catch (error) {
      showNotify('Lỗi kết nối khi tải dữ liệu từ database', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotify = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Tra cứu tên giáo viên dựa vào teacher_id
  const getTeacherName = (teacherId) => {
    if (!teacherId) return 'Chưa phân công';
    const found = teacherList.find(t => t.id === teacherId);
    return found ? (found.name || found.full_name || found.email || teacherId) : teacherId;
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value };
      
      if (field === 'morning_or_afternoon' || field === 'period') {
        const shift = field === 'morning_or_afternoon' ? value : prev.morning_or_afternoon;
        const periodNum = field === 'period' ? Number(value) : prev.period;
        const timeSlot = periodsConfigMap[shift]?.[periodNum];
        
        if (timeSlot) {
          updated.start_time = timeSlot.start;
          updated.end_time = timeSlot.end;
        }
      }
      return updated;
    });
  };

  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    try {
      const headers = await getAuthHeaders();
      const res = await fetch('/api/admin/schedules', {
        method: 'POST',
        headers,
        body: JSON.stringify(formData)
      });
      const result = await res.json();
      if (result.success) {
        showNotify('Thêm lịch học thành công!');
        setShowAddModal(false);
        fetchDataReal();
      } else {
        showNotify(result.message || 'Thêm thất bại', 'error');
      }
    } catch (err) {
      showNotify('Lỗi kết nối server', 'error');
    }
  };

  const handleDateChange = (days) => {
    const d = new Date(selectedDate || new Date());
    d.setDate(d.getDate() + days);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const formatDateLabel = (dateStr) => {
    try {
      if (!dateStr) return "Chọn ngày";
      const date = new Date(dateStr);
      return date.toLocaleDateString("vi-VN", {
        weekday: "long",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch (e) {
      return dateStr;
    }
  };

  const periodsConfig = {
    morning: [
      { period: 1, time: "07:00 - 07:45" },
      { period: 2, time: "07:55 - 08:40" },
      { period: 3, time: "08:50 - 09:35" },
      { period: 4, time: "09:45 - 10:30" },
      { period: 5, time: "10:40 - 11:25" },
    ],
    afternoon: [
      { period: 1, time: "13:00 - 13:45" },
      { period: 2, time: "13:55 - 14:40" },
      { period: 3, time: "14:50 - 15:35" },
      { period: 4, time: "15:45 - 16:30" },
      { period: 5, time: "16:40 - 17:25" },
    ]
  };

  const extractSessionDate = (s) => {
    if (s.session_date) return s.session_date.substring(0, 10);
    if (s.started_at) {
      const d = new Date(s.started_at);
      if (!isNaN(d.getTime())) return d.toISOString().split('T')[0];
    }
    return '';
  };

  const extractStartTime = (s) => {
    if (s.start_time) return s.start_time;
    if (s.started_at) {
      const d = new Date(s.started_at);
      if (!isNaN(d.getTime())) return d.toTimeString().substring(0, 5);
    }
    return '07:00';
  };

  const stats = {
    total: sessions.length,
    morning: sessions.filter(s => (s.session_type || 'morning') === 'morning').length,
    afternoon: sessions.filter(s => (s.session_type || 'afternoon') === 'afternoon').length,
  };

  return (
    <div className="session-management">
      {notification && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-white ${notification.type === 'error' ? 'bg-red-600' : 'bg-green-600'}`} style={{ zIndex: 9999 }}>
          {notification.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Header trang */}
      <div className="session-page-header">
        <div>
          <h1 className="session-page-title">Quản lý Lịch học & Thời khóa biểu</h1>
          <p className="session-page-description">Thời khóa biểu chuẩn khung giờ tiết học THPT và danh sách lớp học</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="session-create-btn">
          <Plus size={16} /> Thêm lịch học
        </button>
      </div>

      {/* Thống kê tổng quan */}
      <div className="session-statistics">
        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">Tổng số tiết / lịch</p>
            <h3 className="session-stat-value">{stats.total}</h3>
          </div>
          <div className="session-stat-icon blue"><Users size={22} /></div>
        </div>
        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">Buổi Sáng</p>
            <h3 className="session-stat-value">{stats.morning}</h3>
          </div>
          <div className="session-stat-icon green"><Clock size={22} /></div>
        </div>
        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">Buổi Chiều</p>
            <h3 className="session-stat-value">{stats.afternoon}</h3>
          </div>
          <div className="session-stat-icon orange"><Calendar size={22} /></div>
        </div>
        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">Trạng thái hệ thống</p>
            <h3 className="session-stat-value" style={{ fontSize: '16px', color: '#16a34a', marginTop: '10px' }}>Hoạt động ổn định</h3>
          </div>
          <div className="session-stat-icon purple"><div className="session-stat-live-dot" /></div>
        </div>
      </div>

      {/* Card chứa bộ điều hướng ngày và lưới thời khóa biểu */}
      <div className="session-calendar-card">
        <div className="session-date-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div className="session-date-navigation" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button onClick={() => handleDateChange(-1)} className="session-date-btn" title="Ngày trước">‹</button>
            <div className="session-current-date">{formatDateLabel(selectedDate)}</div>
            <button onClick={() => handleDateChange(1)} className="session-date-btn" title="Ngày sau">›</button>
            
            {/* Biểu tượng cuốn lịch chọn ngày nhanh */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <div 
                className="session-date-btn" 
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                title="Chọn ngày nhanh"
                onClick={() => {
                  const dateInput = document.getElementById('quick-date-picker');
                  if (dateInput && typeof dateInput.showPicker === 'function') dateInput.showPicker();
                  else if (dateInput) dateInput.click();
                }}
              >
                <Calendar size={18} />
              </div>
              <input 
                id="quick-date-picker"
                type="date"
                value={selectedDate}
                onChange={(e) => { if (e.target.value) setSelectedDate(e.target.value); }}
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer', zIndex: 2 }}
              />
            </div>

            <button onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])} className="session-today-btn">
              Hôm nay
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => setSelectedShift('morning')} className={`session-today-btn ${selectedShift === 'morning' ? 'active' : ''}`}>
              ☀️ Buổi Sáng
            </button>
            <button onClick={() => setSelectedShift('afternoon')} className={`session-today-btn ${selectedShift === 'afternoon' ? 'active' : ''}`}>
              🌙 Buổi Chiều
            </button>
            <button onClick={fetchDataReal} className="session-date-btn" title="Làm mới">
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        {/* Bảng lưới thời khóa biểu */}
        <div className="session-calendar-wrapper" style={{ overflowX: 'auto', padding: '16px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Đang tải dữ liệu từ database...</div>
          ) : classList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>Chưa có lớp học nào trong cơ sở dữ liệu.</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '950px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '12px', borderRight: '1px solid #e2e8f0', width: '150px', textAlign: 'center', color: '#0f172a', fontSize: '14px' }}>Lớp học</th>
                  {periodsConfig[selectedShift].map((p) => (
                    <th key={p.period} style={{ padding: '12px', borderRight: '1px solid #e2e8f0', textAlign: 'center', color: '#475569', fontSize: '13px' }}>
                      <div style={{ fontWeight: 700, color: '#1e293b' }}>Tiết {p.period}</div>
                      <div style={{ fontSize: '11px', fontWeight: 500, color: '#64748b', marginTop: '2px' }}>{p.time}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {classList.map((cls) => {
                  const classId = cls.id;
                  const className = cls.name || cls.class_name || classId;

                  return (
                    <tr key={classId} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '14px', background: '#f8fafc', borderRight: '1px solid #e2e8f0', fontWeight: 700, color: '#2563eb', textAlign: 'center' }}>
                        {className}
                      </td>
                      {periodsConfig[selectedShift].map((p) => {
                        const matchedSession = sessions.find(s => {
                          const sDate = extractSessionDate(s);
                          const sClassId = s.class_id;
                          const sShift = s.session_type || 'morning';
                          
                          let sPeriod = Number(s.period);
                          const timeStr = extractStartTime(s);
                          
                          if (!sPeriod && timeStr) {
                            const [h, m] = timeStr.split(':').map(Number);
                            if (sShift === 'morning') {
                              if (h === 7 && m <= 45) sPeriod = 1;
                              else if ((h === 7 && m >= 55) || (h === 8 && m <= 40)) sPeriod = 2;
                              else if ((h === 8 && m >= 50) || (h === 9 && m <= 35)) sPeriod = 3;
                              else if ((h === 9 && m >= 45) || (h === 10 && m <= 30)) sPeriod = 4;
                              else if (h >= 10) sPeriod = 5;
                            } else {
                              if (h === 13 && m <= 45) sPeriod = 1;
                              else if ((h === 13 && m >= 55) || (h === 14 && m <= 40)) sPeriod = 2;
                              else if ((h === 14 && m >= 50) || (h === 15 && m <= 35)) sPeriod = 3;
                              else if ((h === 15 && m >= 45) || (h === 16 && m <= 30)) sPeriod = 4;
                              else if (h >= 16) sPeriod = 5;
                            }
                          }

                          return sDate === selectedDate && sClassId === classId && sShift === selectedShift && sPeriod === p.period;
                        });

                        return (
                          <td key={p.period} style={{ padding: '6px', borderRight: '1px solid #e2e8f0', verticalAlign: 'top', height: '95px', width: '190px', background: '#fff' }}>
                            {matchedSession ? (
                              <div
                                onClick={() => setMonitorSession({ session: matchedSession, className })}
                                title="Mở bảng giám sát"
                                style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '8px', height: '100%', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', overflow: 'hidden', cursor: 'pointer' }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '4px' }}>
                                  <div style={{ fontWeight: 700, fontSize: '13px', color: '#1e293b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{matchedSession.subject || 'Môn học'}</div>
                                  <SessionStatusBadge status={matchedSession.status} />
                                </div>
                                <div style={{ fontSize: '11px', color: '#475569' }}>Phòng: <strong style={{ color: '#1e293b' }}>{matchedSession.room || cls.room || 'P101'}</strong></div>
                                <div style={{ fontSize: '11px', color: '#475569', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>GV: <strong style={{ color: '#1e293b' }}>{getTeacherName(matchedSession.teacher_id)}</strong></div>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#cbd5e1', fontSize: '12px', border: '1px dashed #f1f5f9', borderRadius: '8px' }}>
                                Trống
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {monitorSession && (
        <SessionMonitorModal
          session={monitorSession.session}
          className={monitorSession.className}
          teacherName={getTeacherName(monitorSession.session.teacher_id)}
          onClose={() => setMonitorSession(null)}
          onStatusChange={fetchDataReal}
        />
      )}

      {/* Modal Thêm Lịch Học */}
      {showAddModal && (
        <div className="session-modal-overlay">
          <div className="session-modal">
            <div className="session-modal-header">
              <div>
                <h2>Thêm lịch học mới</h2>
                <p>Phân bổ lịch học theo đúng khung giờ và lớp học.</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="session-modal-close"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateSchedule}>
              <div className="session-modal-content">
                <div className="session-form-group">
                  <label>Môn học *</label>
                  <input 
                    type="text" required className="session-form-control"
                    value={formData.subject} onChange={(e) => handleFormChange('subject', e.target.value)}
                    placeholder="Ví dụ: Toán, Ngữ Văn..."
                  />
                </div>
                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Ngày học *</label>
                    <input 
                      type="date" required className="session-form-control"
                      value={formData.session_date} onChange={(e) => handleFormChange('session_date', e.target.value)}
                    />
                  </div>
                  <div className="session-form-group">
                    <label>Buổi học</label>
                    <select 
                      className="session-form-control"
                      value={formData.morning_or_afternoon} 
                      onChange={(e) => {
                        const newShift = e.target.value;
                        const defaultSlot = periodsConfigMap[newShift]?.[1] || { start: '07:00', end: '07:45' };
                        setFormData(prev => ({
                          ...prev,
                          morning_or_afternoon: newShift,
                          period: 1,
                          start_time: defaultSlot.start,
                          end_time: defaultSlot.end
                        }));
                      }}
                    >
                      <option value="morning">Buổi Sáng</option>
                      <option value="afternoon">Buổi Chiều</option>
                    </select>
                  </div>
                </div>

                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Tiết số (1-5) *</label>
                    <select 
                      className="session-form-control"
                      value={formData.period} 
                      onChange={(e) => handleFormChange('period', Number(e.target.value))}
                    >
                      {Object.entries(periodsConfigMap[formData.morning_or_afternoon] || {}).map(([pNum, slot]) => (
                        <option key={pNum} value={Number(pNum)}>
                          Tiết {pNum} ({slot.start} - {slot.end})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="session-form-group">
                    <label>Phòng học *</label>
                    <select 
                      required className="session-form-control"
                      value={formData.room} onChange={(e) => handleFormChange('room', e.target.value)}
                    >
                      <option value="">-- Chọn phòng học --</option>
                      {roomList.map(room => (
                        <option key={room.id} value={room.id}>{room.name || room.id}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Thời gian bắt đầu</label>
                    <input 
                      type="time" className="session-form-control"
                      value={formData.start_time} 
                      onChange={(e) => handleFormChange('start_time', e.target.value)}
                    />
                  </div>
                  <div className="session-form-group">
                    <label>Thời gian kết thúc</label>
                    <input 
                      type="time" className="session-form-control"
                      value={formData.end_time} 
                      onChange={(e) => handleFormChange('end_time', e.target.value)}
                    />
                  </div>
                </div>

                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Chọn Lớp học *</label>
                    <select 
                      required className="session-form-control"
                      value={formData.class_id} onChange={(e) => handleFormChange('class_id', e.target.value)}
                    >
                      <option value="">-- Chọn lớp học --</option>
                      {classList.map(cls => (
                        <option key={cls.id} value={cls.id}>{cls.name || cls.class_name || cls.id}</option>
                      ))}
                    </select>
                  </div>
                  <div className="session-form-group">
                    <label>Giáo viên giảng dạy *</label>
                    <select 
                      required className="session-form-control"
                      value={formData.teacher_id} onChange={(e) => handleFormChange('teacher_id', e.target.value)}
                    >
                      <option value="">-- Chọn giáo viên --</option>
                      {teacherList.map(teacher => (
                        <option key={teacher.id} value={teacher.id}>{teacher.name || teacher.full_name || teacher.id}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              <div className="session-modal-footer">
                <button type="button" onClick={() => setShowAddModal(false)} className="session-secondary-btn">Hủy</button>
                <button type="submit" className="session-primary-btn">Lưu lịch học</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}