import { useState } from "react";

import Icon from "../common/Icon";
import { getAuthHeaders } from "../../utils/AuthSession";

// Nhập danh sách từ file Excel (.xlsx) cho trang giáo viên và học sinh. File có dòng sai thì backend không thêm
// ai và trả lỗi từng dòng; người đã có trong hệ thống được bỏ qua và hiện ra trước khi đóng.
const ImportFileModal = ({ title, columns, url, label, onClose, onImported }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setErrors(["Vui lòng chọn file Excel (.xlsx)."]);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setErrors([]);
    try {
      const headers = await getAuthHeaders();
      delete headers["Content-Type"]; // trình duyệt tự đặt multipart/form-data kèm boundary

      const response = await fetch(url, { method: "POST", headers, body: formData });
      const data = await response.json();

      if (!response.ok || !data.success) {
        setErrors([data.message || "Nhập file thất bại.", ...(data.errors || [])]);
      } else if (data.duplicates?.length) {
        setResult(data);
      } else {
        onImported(data.message);
      }
    } catch {
      setErrors(["Lỗi kết nối máy chủ."]);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="edit-teacher-overlay" style={{ zIndex: 99999 }}>
        <div className="edit-teacher-modal" style={{ maxWidth: "450px", padding: "24px", borderRadius: "16px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: "16px" }}>
            <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "#fff7ed", color: "#ea580c", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Icon name="alertCircle" size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: "0 0 8px 0", fontSize: "17px", fontWeight: "700", color: "#0f172a" }}>
                Thông tin trùng lặp dữ liệu
              </h3>
              <p style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#475569", lineHeight: "1.5" }}>
                Đã thêm thành công <b>{result.success_count}</b> {label} mới. Tuy nhiên, các {label} sau đã tồn tại trong hệ thống:
              </p>

              <div style={{ maxHeight: "150px", overflowY: "auto", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "10px 14px", marginBottom: "20px" }}>
                <ul style={{ margin: 0, paddingLeft: "18px", color: "#334155", fontSize: "13px" }}>
                  {result.duplicates.map((name, idx) => (
                    <li key={idx} style={{ marginBottom: "4px", fontWeight: "500" }}>{name}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
            <button
              type="button"
              className="edit-teacher-save"
              style={{ backgroundColor: "#2563eb", width: "100px", height: "38px" }}
              onClick={() => onImported(result.message)}
            >
              Đã hiểu
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="edit-teacher-overlay">
      <div className="edit-teacher-modal" style={{ maxWidth: "500px" }}>
        <div className="edit-teacher-header">
          <div>
            <h2>{title}</h2>
            <p>File Excel (.xlsx), đọc sheet đầu tiên. Dòng tiêu đề gồm các cột: {columns} (* là bắt buộc).</p>
          </div>
          <button type="button" className="edit-teacher-close" onClick={onClose} aria-label="Đóng">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="edit-teacher-form">
          <div className="edit-teacher-field">
            <label htmlFor="import-file-input">Chọn file dữ liệu *</label>

            <div className="file-dropzone">
              <input
                type="file"
                id="import-file-input"
                accept=".xlsx"
                onChange={(e) => {
                  setFile(e.target.files[0] || null);
                  setErrors([]);
                }}
                className="file-input-hidden"
              />
              <label htmlFor="import-file-input" className="file-dropzone-label">
                <div className="file-dropzone-icon">
                  <Icon name="upload" size={28} />
                </div>
                {file ? (
                  <div className="file-selected-info">
                    <strong style={{ color: "#2563eb", fontSize: "13px" }}>{file.name}</strong>
                    <span>Nhấp hoặc chọn file khác để thay đổi</span>
                  </div>
                ) : (
                  <div className="file-placeholder-info">
                    <strong>Nhấp để chọn file</strong> hoặc kéo thả file vào đây
                    <small>(.xlsx)</small>
                  </div>
                )}
              </label>
            </div>
          </div>

          {errors.length > 0 && (
            <ul style={{ margin: "0 0 18px 0", padding: "10px 14px 10px 30px", maxHeight: "160px", overflowY: "auto", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", color: "#b91c1c", fontSize: "13px", lineHeight: "1.5" }}>
              {errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          )}

          <div className="edit-teacher-actions">
            <button type="button" className="edit-teacher-cancel" onClick={onClose} disabled={loading}>
              Hủy
            </button>
            <button
              type="submit"
              className="import-account-button"
              style={{ height: "38px", padding: "0 18px", fontSize: "12px" }}
              disabled={loading}
            >
              {loading ? "Đang xử lý..." : "Tải lên & Xử lý"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ImportFileModal;
