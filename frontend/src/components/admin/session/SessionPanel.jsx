import React, { useState, useEffect } from 'react';
import { 
  Users, Calendar, Clock, Search, RefreshCw, 
  Plus, Eye, Edit, Trash2, X, CheckCircle, AlertCircle 
} from 'lucide-react';
import { getAuth, onAuthStateChanged } from 'firebase/auth';

export default function SessionDetailPanel() {
  const [sessions, setSessions] = useState([]);
  const [classList, setClassList] = useState([]);
  const [teacherList, setTeacherList] = useState([]);
  const [roomList, setRoomList] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]); 
  const [selectedShift, setSelectedShift] = useState('morning'); // 'morning' | 'afternoon'
  const [viewMode, setViewMode] = useState('class'); // 'class' | 'teacher'
  const [timeFilterMode, setTimeFilterMode] = useState('day'); // 'day' | 'week' | 'month'
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedSessionDetail, setSelectedSessionDetail] = useState(null);
  
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

  const initialFormState = {
    class_id: '',
    teacher_id: '',
    subject: '',
    is_custom_subject: false,
    custom_subject_name: '',
    session_date: new Date().toISOString().split('T')[0],
    room: '',
    repeat_count: 5,
    day_configs: {
      1: { active: true, shift: 'morning', period: 1 },
      3: { active: true, shift: 'morning', period: 1 }
    }
  };

  const [formData, setFormData] = useState(initialFormState);
  const [notification, setNotification] = useState(null);

  const getAuthHeaders = async () => {
    const headers = { 'Content-Type': 'application/json' };
    try {
      const auth = getAuth();
      const currentUser = auth.currentUser;
      if (currentUser) {
        const token = await currentUser.getIdToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
      } else {
        const token = localStorage.getItem('token') || localStorage.getItem('firebaseToken') || sessionStorage.getItem('token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (e) {
      console.error("Lỗi lấy token:", e);
    }
    return headers;
  };

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

      if (scheduleResult.success) setSessions(scheduleResult.data || []);
      if (classResult.success) setClassList(classResult.data || []);
      if (teacherResult.success) setTeacherList(teacherResult.data || []);
      if (roomResult.success) setRoomList(roomResult.data || []);
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

  const resetForm = () => {
    setFormData({
      ...initialFormState,
      session_date: new Date().toISOString().split('T')[0]
    });
  };

  const getTeacherName = (teacherId) => {
    if (!teacherId) return 'Chưa phân công';
    const found = teacherList.find(t => t.id === teacherId);
    return found ? (found.name || found.full_name || found.email || teacherId) : teacherId;
  };

  const getClassName = (classId) => {
    if (!classId) return 'Chưa rõ lớp';
    const found = classList.find(c => c.id === classId);
    return found ? (found.name || found.class_name || classId) : classId;
  };

  const getSelectedTeacherSubjects = () => {
    if (!formData.teacher_id) return [];
    const foundTeacher = teacherList.find(t => t.id === formData.teacher_id);
    if (!foundTeacher || !foundTeacher.subject) return [];
    if (Array.isArray(foundTeacher.subject)) return foundTeacher.subject;
    return String(foundTeacher.subject).split(',').map(s => s.trim()).filter(Boolean);
  };

  const handleTeacherChange = (teacherId) => {
    setFormData(prev => {
      const foundTeacher = teacherList.find(t => t.id === teacherId);
      let defaultSubject = '';
      if (foundTeacher && foundTeacher.subject) {
        defaultSubject = Array.isArray(foundTeacher.subject) 
          ? foundTeacher.subject[0] 
          : String(foundTeacher.subject).split(',')[0].trim();
      }
      return {
        ...prev,
        teacher_id: teacherId,
        subject: defaultSubject,
        is_custom_subject: false,
        custom_subject_name: ''
      };
    });
  };

  const toggleDaySelection = (dayVal) => {
    setFormData(prev => {
      const currentConfigs = { ...prev.day_configs };
      if (currentConfigs[dayVal]) {
        delete currentConfigs[dayVal];
      } else {
        currentConfigs[dayVal] = { active: true, shift: 'morning', period: 1 };
      }
      return { ...prev, day_configs: currentConfigs };
    });
  };

  const handleDayConfigChange = (dayVal, field, value) => {
    setFormData(prev => ({
      ...prev,
      day_configs: {
        ...prev.day_configs,
        [dayVal]: {
          ...prev.day_configs[dayVal],
          [field]: value
        }
      }
    }));
  };

  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    const finalSubject = formData.is_custom_subject 
      ? formData.custom_subject_name.trim() 
      : formData.subject;

    if (!finalSubject) {
      showNotify('Vui lòng chọn hoặc nhập môn học.', 'error');
      return;
    }

    if (Object.keys(formData.day_configs).length === 0) {
      showNotify('Vui lòng chọn ít nhất 1 ngày học trong tuần.', 'error');
      return;
    }

    try {
      const headers = await getAuthHeaders();
      const payload = {
        class_id: formData.class_id,
        teacher_id: formData.teacher_id,
        subject: finalSubject,
        session_date: formData.session_date,
        room: formData.room,
        repeat_count: Number(formData.repeat_count) || 1,
        day_configs: formData.day_configs
      };

      const res = await fetch('/api/admin/schedules', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      const result = await res.json();

      if (result.success) {
        showNotify(result.message || 'Thêm lịch học thành công!');
        setShowAddModal(false);
        resetForm();
        fetchDataReal();
      } else {
        showNotify(result.message || 'Thêm thất bại', 'error');
      }
    } catch (err) {
      showNotify('Lỗi kết nối máy chủ', 'error');
    }
  };

  const handleTimeNavigation = (direction) => {
    const d = new Date(selectedDate || new Date());
    if (timeFilterMode === 'day') {
      d.setDate(d.getDate() + direction);
    } else if (timeFilterMode === 'week') {
      d.setDate(d.getDate() + direction * 7);
    } else if (timeFilterMode === 'month') {
      d.setMonth(d.getMonth() + direction);
    }
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const formatDateLabel = () => {
    try {
      if (!selectedDate) return "Chọn ngày";
      const date = new Date(selectedDate);
      if (timeFilterMode === 'day') {
        return date.toLocaleDateString("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });
      } else if (timeFilterMode === 'week') {
        const startOfWeek = new Date(date);
        startOfWeek.setDate(date.getDate() - date.getDay() + (date.getDay() === 0 ? -6 : 1));
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 5);
        return `Tuần: ${startOfWeek.toLocaleDateString("vi-VN", {day: "2-digit", month: "2-digit"})} - ${endOfWeek.toLocaleDateString("vi-VN", {day: "2-digit", month: "2-digit", year: "numeric"})}`;
      } else {
        return date.toLocaleDateString("vi-VN", { month: "long", year: "numeric" });
      }
    } catch (e) {
      return selectedDate;
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

  const getDaysInCurrentWeek = () => {
    const curr = new Date(selectedDate);
    const week = [];
    const firstDayOfWeek = curr.getDate() - curr.getDay() + (curr.getDay() === 0 ? -6 : 1);
    
    for (let i = 0; i < 6; i++) {
      const nextDay = new Date(curr.setDate(firstDayOfWeek + i));
      week.push({
        dateStr: nextDay.toISOString().split('T')[0],
        label: nextDay.toLocaleDateString("vi-VN", { weekday: "short", day: "2-digit", month: "2-digit" })
      });
    }
    return week;
  };

  const extractSessionDate = (s) => {
    if (s.session_date) return s.session_date.substring(0, 10);
    if (s.started_at) {
      const d = new Date(s.started_at);
      if (!isNaN(d.getTime())) return d.toISOString().split('T')[0];
    }
    return '';
  };

  const getSessionStatusStyle = (sessionDate, startTimeStr, endTimeStr) => {
    const todayStr = new Date().toISOString().split('T')[0];
    const now = new Date();
    const currentTimeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    if (sessionDate < todayStr) {
      return { bg: '#f1f5f9', border: '#cbd5e1', textBg: '#475569', statusText: 'Đã học xong', statusColor: '#64748b' };
    }
    if (sessionDate > todayStr) {
      return { bg: '#eff6ff', border: '#bfdbfe', textBg: '#1e40af', statusText: 'Sắp tới', statusColor: '#2563eb' };
    }
    if (currentTimeStr > endTimeStr) {
      return { bg: '#f1f5f9', border: '#cbd5e1', textBg: '#475569', statusText: 'Đã học xong', statusColor: '#64748b' };
    } else if (currentTimeStr >= startTimeStr && currentTimeStr <= endTimeStr) {
      return { bg: '#dcfce7', border: '#86efac', textBg: '#15803d', statusText: 'Đang hoạt động', statusColor: '#16a34a' };
    } else {
      return { bg: '#eff6ff', border: '#bfdbfe', textBg: '#1e40af', statusText: 'Sắp tới', statusColor: '#2563eb' };
    }
  };

  const stats = {
    total: sessions.length,
    morning: sessions.filter(s => (s.session_type || 'morning') === 'morning').length,
    afternoon: sessions.filter(s => (s.session_type || 'afternoon') === 'afternoon').length,
  };

  const teacherSubjects = getSelectedTeacherSubjects();
  const currentWeekDays = getDaysInCurrentWeek();

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

      {/* Thống kê */}
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

      {/* Card lịch học */}
      <div className="session-calendar-card">
        <div className="session-date-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
          
          {/* Nút điều hướng < > và bộ lọc Ngày / Tuần / Tháng */}
          <div className="session-date-navigation" style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', background: '#f1f5f9', padding: '3px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <button onClick={() => setTimeFilterMode('day')} style={{ padding: '5px 10px', fontSize: '12px', fontWeight: 600, borderRadius: '6px', border: 'none', background: timeFilterMode === 'day' ? '#2563eb' : 'transparent', color: timeFilterMode === 'day' ? '#fff' : '#64748b', cursor: 'pointer' }}>Ngày</button>
              <button onClick={() => setTimeFilterMode('week')} style={{ padding: '5px 10px', fontSize: '12px', fontWeight: 600, borderRadius: '6px', border: 'none', background: timeFilterMode === 'week' ? '#2563eb' : 'transparent', color: timeFilterMode === 'week' ? '#fff' : '#64748b', cursor: 'pointer' }}>Tuần</button>
              <button onClick={() => setTimeFilterMode('month')} style={{ padding: '5px 10px', fontSize: '12px', fontWeight: 600, borderRadius: '6px', border: 'none', background: timeFilterMode === 'month' ? '#2563eb' : 'transparent', color: timeFilterMode === 'month' ? '#fff' : '#64748b', cursor: 'pointer' }}>Tháng</button>
            </div>

            <button 
              onClick={() => handleTimeNavigation(-1)} 
              className="session-date-btn" 
              title="Trước"
              style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', padding: 0 }}
            >
              ‹
            </button>
            <div className="session-current-date" style={{ fontWeight: '600', color: '#0f172a', fontSize: '14px' }}>{formatDateLabel()}</div>
            <button 
              onClick={() => handleTimeNavigation(1)} 
              className="session-date-btn" 
              title="Sau"
              style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', padding: 0 }}
            >
              ›
            </button>
            
            <button onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])} className="session-today-btn">
              Hôm nay
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            {/* Chế độ Theo lớp / Theo giáo viên */}
            <div style={{ display: 'flex', background: '#f1f5f9', padding: '3px', borderRadius: '8px', border: '1px solid #e2e8f0', minWidth: '220px' }}>
              <button 
                onClick={() => setViewMode('class')} 
                style={{ flex: 1, textAlign: 'center', padding: '6px 12px', fontSize: '13px', fontWeight: 600, borderRadius: '6px', border: 'none', background: viewMode === 'class' ? '#2563eb' : 'transparent', color: viewMode === 'class' ? '#fff' : '#64748b', cursor: 'pointer' }}
              >
                Theo lớp
              </button>
              <button 
                onClick={() => setViewMode('teacher')} 
                style={{ flex: 1, textAlign: 'center', padding: '6px 12px', fontSize: '13px', fontWeight: 600, borderRadius: '6px', border: 'none', background: viewMode === 'teacher' ? '#2563eb' : 'transparent', color: viewMode === 'teacher' ? '#fff' : '#64748b', cursor: 'pointer' }}
              >
                Theo giáo viên
              </button>
            </div>

            {timeFilterMode === 'day' && (
              <>
                <button onClick={() => setSelectedShift('morning')} className={`session-today-btn ${selectedShift === 'morning' ? 'active' : ''}`}>Buổi Sáng</button>
                <button onClick={() => setSelectedShift('afternoon')} className={`session-today-btn ${selectedShift === 'afternoon' ? 'active' : ''}`}>Buổi Chiều</button>
              </>
            )}
            <button onClick={fetchDataReal} className="session-date-btn" title="Làm mới" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px' }}>
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        {/* LƯỚI HIỂN THỊ THỜI KHÓA BIỂU (Tối ưu hiển thị Sáng/Chiều cho Tuần và Tháng) */}
        <div className="session-calendar-wrapper" style={{ overflowX: 'auto', padding: '16px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>Đang tải dữ liệu từ database...</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '950px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '12px', borderRight: '1px solid #e2e8f0', width: '160px', textAlign: 'center', color: '#0f172a', fontSize: '14px' }}>
                    {viewMode === 'class' ? 'Lớp học' : 'Giáo viên'}
                  </th>
                  
                  {/* Xem theo Ngày */}
                  {timeFilterMode === 'day' && periodsConfig[selectedShift].map((p) => (
                    <th key={p.period} style={{ padding: '12px', borderRight: '1px solid #e2e8f0', textAlign: 'center', color: '#475569', fontSize: '13px' }}>
                      <div style={{ fontWeight: 700, color: '#1e293b' }}>Tiết {p.period}</div>
                      <div style={{ fontSize: '11px', fontWeight: 500, color: '#64748b', marginTop: '2px' }}>{p.time}</div>
                    </th>
                  ))}

                  {/* Xem theo Tuần */}
                  {timeFilterMode === 'week' && currentWeekDays.map((dayObj) => (
                    <th key={dayObj.dateStr} style={{ padding: '12px', borderRight: '1px solid #e2e8f0', textAlign: 'center', color: '#475569', fontSize: '13px' }}>
                      <div style={{ fontWeight: 700, color: '#1e293b' }}>{dayObj.label}</div>
                    </th>
                  ))}

                  {/* Xem theo Tháng */}
                  {timeFilterMode === 'month' && (
                    <th style={{ padding: '12px', textAlign: 'center', color: '#475569', fontSize: '13px' }}>
                      Danh sách các buổi học trong tháng (Sáng & Chiều)
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {(viewMode === 'class' ? classList : teacherList).map((item) => {
                  const itemId = item.id;
                  const itemName = viewMode === 'class' ? (item.name || item.class_name || itemId) : (item.name || item.full_name || itemId);

                  return (
                    <tr key={itemId} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '14px', background: '#f8fafc', borderRight: '1px solid #e2e8f0', fontWeight: 700, color: '#2563eb', textAlign: 'center' }}>
                        {itemName}
                      </td>

                      {/* HIỂN THỊ THEO NGÀY */}
                      {timeFilterMode === 'day' && periodsConfig[selectedShift].map((p) => {
                        const matchedSession = sessions.find(s => {
                          const sDate = extractSessionDate(s);
                          const sShift = s.session_type || 'morning';
                          const sPeriod = Number(s.period || 1);
                          const matchesCondition = viewMode === 'class' ? (s.class_id === itemId) : (s.teacher_id === itemId);
                          return sDate === selectedDate && matchesCondition && sShift === selectedShift && sPeriod === p.period;
                        });

                        const sessionStyle = matchedSession ? getSessionStatusStyle(selectedDate, p.time.split(' - ')[0], p.time.split(' - ')[1]) : null;

                        return (
                          <td key={p.period} style={{ padding: '6px', borderRight: '1px solid #e2e8f0', verticalAlign: 'top', height: '95px', width: '190px', background: '#fff' }}>
                            {matchedSession ? (
                              <div 
                                onClick={() => setSelectedSessionDetail(matchedSession)}
                                style={{ background: sessionStyle.bg, border: `1px solid ${sessionStyle.border}`, borderRadius: '8px', padding: '8px', height: '100%', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <div style={{ fontWeight: 700, fontSize: '13px', color: sessionStyle.textBg, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{matchedSession.subject}</div>
                                  <span style={{ fontSize: '10px', fontWeight: 'bold', color: sessionStyle.statusColor, background: '#fff', padding: '2px 6px', borderRadius: '4px' }}>{sessionStyle.statusText}</span>
                                </div>
                                <div style={{ fontSize: '11px', color: '#475569' }}>
                                  {viewMode === 'class' ? 'GV: ' : 'Lớp: '} <strong style={{ color: '#1e293b' }}>{viewMode === 'class' ? getTeacherName(matchedSession.teacher_id) : getClassName(matchedSession.class_id)}</strong>
                                </div>
                                <div style={{ fontSize: '11px', color: '#475569' }}>Phòng: <strong style={{ color: '#1e293b' }}>{matchedSession.room || '301'}</strong></div>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#cbd5e1', fontSize: '12px', border: '1px dashed #f1f5f9', borderRadius: '8px' }}>Trống</div>
                            )}
                          </td>
                        );
                      })}

                      {/* HIỂN THỊ THEO TUẦN (Tối ưu hiển thị Sáng/Chiều rõ ràng) */}
                      {timeFilterMode === 'week' && currentWeekDays.map((dayObj) => {
                        const daySessions = sessions.filter(s => {
                          const sDate = extractSessionDate(s);
                          const matchesCondition = viewMode === 'class' ? (s.class_id === itemId) : (s.teacher_id === itemId);
                          return sDate === dayObj.dateStr && matchesCondition;
                        });

                        return (
                          <td key={dayObj.dateStr} style={{ padding: '6px', borderRight: '1px solid #e2e8f0', verticalAlign: 'top', minHeight: '95px', width: '150px', background: '#fff' }}>
                            {daySessions.length > 0 ? (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {daySessions.map(sess => {
                                  const isMorning = (sess.session_type || 'morning') === 'morning';
                                  return (
                                    <div 
                                      key={sess.id} 
                                      onClick={() => setSelectedSessionDetail(sess)}
                                      style={{ 
                                        background: isMorning ? '#eff6ff' : '#fef3c7', 
                                        border: `1px solid ${isMorning ? '#bfdbfe' : '#fde68a'}`, 
                                        borderRadius: '6px', 
                                        padding: '6px', 
                                        cursor: 'pointer', 
                                        fontSize: '11px' 
                                      }}
                                    >
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <strong style={{ color: isMorning ? '#1e40af' : '#b45309' }}>{sess.subject}</strong>
                                        <span style={{ fontSize: '9px', fontWeight: 'bold', padding: '1px 4px', background: '#fff', borderRadius: '3px', color: isMorning ? '#2563eb' : '#d97706' }}>
                                          {isMorning ? 'Sáng' : 'Chiều'}
                                        </span>
                                      </div>
                                      <div style={{ color: '#475569', marginTop: '2px' }}>Tiết {sess.period} • P.{sess.room || '301'}</div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <div style={{ textAlign: 'center', color: '#cbd5e1', fontSize: '11px', padding: '20px 0' }}>Không có lịch</div>
                            )}
                          </td>
                        );
                      })}

                      {/* HIỂN THỊ THEO THÁNG (Tối ưu phân biệt Sáng/Chiều trực quan) */}
                      {timeFilterMode === 'month' && (
                        <td style={{ padding: '10px', background: '#fff' }}>
                          {(() => {
                            const currentMonthPrefix = selectedDate ? selectedDate.substring(0, 7) : ''; 
                            const monthSessions = sessions.filter(s => {
                              const sDate = extractSessionDate(s);
                              const matchesCondition = viewMode === 'class' ? (s.class_id === itemId) : (s.teacher_id === itemId);
                              return sDate && sDate.startsWith(currentMonthPrefix) && matchesCondition;
                            });
                            return (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {monthSessions.length > 0 ? monthSessions.map(sess => {
                                  const sDate = extractSessionDate(sess);
                                  const dayPart = sDate.length >= 10 ? sDate.substring(8, 10) : '01';
                                  const monthPart = sDate.length >= 7 ? sDate.substring(5, 7) : '01';
                                  const isMorning = (sess.session_type || 'morning') === 'morning';
                                  
                                  return (
                                    <span 
                                      key={sess.id} 
                                      onClick={() => setSelectedSessionDetail(sess)}
                                      style={{ 
                                        background: isMorning ? '#f1f5f9' : '#fef9c3', 
                                        border: `1px solid ${isMorning ? '#cbd5e1' : '#fde047'}`, 
                                        borderRadius: '4px', 
                                        padding: '4px 8px', 
                                        fontSize: '12px', 
                                        cursor: 'pointer',
                                        display: 'inline-flex',
                                        alignItem: 'center',
                                        gap: '4px'
                                      }}
                                    >
                                      <strong>{dayPart}/{monthPart}:</strong> {sess.subject || 'Môn học'} 
                                      <span style={{ fontSize: '10px', color: isMorning ? '#2563eb' : '#d97706', fontWeight: 600 }}>
                                        ({isMorning ? 'Sáng' : 'Chiều'} - Tiết {sess.period || 1})
                                      </span>
                                    </span>
                                  );
                                }) : <span style={{ color: '#94a3b8', fontSize: '12px' }}>Chưa có lịch học trong tháng này.</span>}
                              </div>
                            );
                          })()}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* MODAL THÊM LỊCH HỌC MỚI */}
      {showAddModal && (
        <div className="session-modal-overlay">
          <div className="session-modal" style={{ maxWidth: '620px' }}>
            <div className="session-modal-header">
              <div>
                <h2>Thêm lịch học mới</h2>
                <p>Phân bổ lịch học tự động theo tuần, số lần lặp lại và tiết học.</p>
              </div>
              <button onClick={() => { setShowAddModal(false); resetForm(); }} className="session-modal-close"><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateSchedule}>
              <div className="session-modal-content" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Giáo viên giảng dạy *</label>
                    <select required className="session-form-control" value={formData.teacher_id} onChange={(e) => handleTeacherChange(e.target.value)}>
                      <option value="">-- Chọn giáo viên --</option>
                      {teacherList.map(teacher => (
                        <option key={teacher.id} value={teacher.id}>{teacher.name || teacher.full_name || teacher.id}</option>
                      ))}
                    </select>
                  </div>

                  <div className="session-form-group">
                    <label>Môn học *</label>
                    {!formData.is_custom_subject ? (
                      <select required className="session-form-control" value={formData.subject} onChange={(e) => {
                        if (e.target.value === '__OTHER__') {
                          setFormData(prev => ({ ...prev, is_custom_subject: true, custom_subject_name: '' }));
                        } else {
                          setFormData(prev => ({ ...prev, subject: e.target.value }));
                        }
                      }}>
                        <option value="">-- Chọn môn học --</option>
                        {teacherSubjects.map((sub, i) => (<option key={i} value={sub}>{sub}</option>))}
                        <option value="__OTHER__">+ Môn học khác / Dạy thế...</option>
                      </select>
                    ) : (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <input type="text" required className="session-form-control" placeholder="Nhập tên môn học..." value={formData.custom_subject_name} onChange={(e) => setFormData(prev => ({ ...prev, custom_subject_name: e.target.value }))} />
                        <button type="button" className="session-secondary-btn" style={{ padding: '0 10px', fontSize: '12px' }} onClick={() => setFormData(prev => ({ ...prev, is_custom_subject: false }))}>Chọn lại</button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="session-form-grid">
                  <div className="session-form-group">
                    <label>Chọn Lớp học *</label>
                    <select required className="session-form-control" value={formData.class_id} onChange={(e) => setFormData(prev => ({ ...prev, class_id: e.target.value }))}>
                      <option value="">-- Chọn lớp học --</option>
                      {classList.map(cls => (<option key={cls.id} value={cls.id}>{cls.name || cls.class_name || cls.id}</option>))}
                    </select>
                  </div>

                  <div className="session-form-group">
                    <label>Phòng học *</label>
                    <select required className="session-form-control" value={formData.room} onChange={(e) => setFormData(prev => ({ ...prev, room: e.target.value }))}>
                      <option value="">-- Chọn phòng học --</option>
                      {roomList.map(room => (<option key={room.id} value={room.id}>{room.name || room.id}</option>))}
                    </select>
                  </div>
                </div>

                <div className="session-form-group">
                  <label>Ngày bắt đầu (Buổi đầu tiên) *</label>
                  <input type="date" required className="session-form-control" value={formData.session_date} onChange={(e) => setFormData(prev => ({ ...prev, session_date: e.target.value }))} />
                </div>

                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <label style={{ fontSize: '13px', fontWeight: '600', color: '#1e293b' }}>Chọn các ngày học trong tuần (Tùy chỉnh tiết riêng từng ngày)</label>
                  
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {[
                      { label: 'Thứ 2', val: 1 }, { label: 'Thứ 3', val: 2 }, { label: 'Thứ 4', val: 3 },
                      { label: 'Thứ 5', val: 4 }, { label: 'Thứ 6', val: 5 }, { label: 'Thứ 7', val: 6 },
                    ].map(day => {
                      const isSelected = Boolean(formData.day_configs[day.val]);
                      return (
                        <button key={day.val} type="button" onClick={() => toggleDaySelection(day.val)} style={{ padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: '600', border: isSelected ? '1px solid #2563eb' : '1px solid #cbd5e1', background: isSelected ? '#2563eb' : '#fff', color: isSelected ? '#fff' : '#475569', cursor: 'pointer' }}>
                          {day.label}
                        </button>
                      );
                    })}
                  </div>

                  {Object.keys(formData.day_configs).length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                      {Object.keys(formData.day_configs).sort().map(dayKey => {
                        const dayNum = Number(dayKey);
                        const dayNames = { 1: 'Thứ 2', 2: 'Thứ 3', 3: 'Thứ 4', 4: 'Thứ 5', 5: 'Thứ 6', 6: 'Thứ 7' };
                        const config = formData.day_configs[dayKey];
                        return (
                          <div key={dayKey} style={{ display: 'flex', alignItems: 'center', gap: '10px', background: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                            <span style={{ fontSize: '12px', fontWeight: '700', color: '#2563eb', minWidth: '55px' }}>{dayNames[dayNum]}:</span>
                            <select className="session-filter-select" style={{ height: '32px', fontSize: '12px', flex: 1 }} value={config.shift} onChange={(e) => handleDayConfigChange(dayKey, 'shift', e.target.value)}>
                              <option value="morning">Buổi Sáng</option>
                              <option value="afternoon">Buổi Chiều</option>
                            </select>
                            <select className="session-filter-select" style={{ height: '32px', fontSize: '12px', flex: 1 }} value={config.period} onChange={(e) => handleDayConfigChange(dayKey, 'period', Number(e.target.value))}>
                              {Object.entries(periodsConfigMap[config.shift] || {}).map(([pNum, slot]) => (
                                <option key={pNum} value={Number(pNum)}>Tiết {pNum} ({slot.start} - {slot.end})</option>
                              ))}
                            </select>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '13px', color: '#475569', fontWeight: '500' }}>Tổng số lần lặp lại (số buổi học):</span>
                    <input type="number" min="1" max="100" className="session-form-control" style={{ width: '80px', textAlign: 'center', fontWeight: '700', height: '36px' }} value={formData.repeat_count} onChange={(e) => setFormData(prev => ({ ...prev, repeat_count: Math.max(1, Number(e.target.value)) }))} />
                  </div>
                </div>

              </div>

              <div className="session-modal-footer">
                <button type="button" onClick={() => { setShowAddModal(false); resetForm(); }} className="session-secondary-btn">Hủy</button>
                <button type="submit" className="session-primary-btn">Tạo lịch tự động ({formData.repeat_count} buổi)</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL XEM CHI TIẾT TIẾT HỌC */}
      {selectedSessionDetail && (
        <div className="session-modal-overlay" onClick={() => setSelectedSessionDetail(null)}>
          <div className="session-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '520px' }}>
            <div className="session-modal-header">
              <div>
                <h2>Chi tiết tiết học</h2>
                <p>Thông tin phòng học, giáo viên và lớp học.</p>
              </div>
              <button onClick={() => setSelectedSessionDetail(null)} className="session-modal-close"><X size={18} /></button>
            </div>
            <div className="session-modal-content" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ color: '#64748b' }}>Môn học:</span>
                <strong style={{ color: '#2563eb', fontSize: '15px' }}>{selectedSessionDetail.subject || 'Chưa cập nhật'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ color: '#64748b' }}>Lớp học:</span>
                <strong style={{ color: '#0f172a' }}>{getClassName(selectedSessionDetail.class_id)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ color: '#64748b' }}>Giáo viên giảng dạy:</span>
                <strong style={{ color: '#0f172a' }}>{getTeacherName(selectedSessionDetail.teacher_id)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ color: '#64748b' }}>Phòng học:</span>
                <strong style={{ color: '#0f172a' }}>{selectedSessionDetail.room || '301'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}>
                <span style={{ color: '#64748b' }}>Buổi & Ngày học:</span>
                <strong style={{ color: '#0f172a' }}>{selectedSessionDetail.session_date} ({selectedSessionDetail.session_type === 'afternoon' ? 'Buổi Chiều' : 'Buổi Sáng'} - Tiết {selectedSessionDetail.period})</strong>
              </div>
            </div>
            <div className="session-modal-footer">
              <button type="button" className="session-secondary-btn" onClick={() => setSelectedSessionDetail(null)}>Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}