import Icon from "../../common/Icon";

const AddCameraForm = ({
    onClose,
    onSubmit,
}) => {
    const handleSubmit = (event) => {
        event.preventDefault();

        const formData = new FormData(event.currentTarget);

        onSubmit({
            room_id: formData.get("room_id").trim(),
            camera_name: formData.get("camera_name").trim(),
            ip_address: formData.get("ip_address").trim(),
            rtsp_port: formData.get("rtsp_port").trim(),
        });
    };

    return (
        <div className="camera-modal-overlay">
            <div
                className="camera-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="add-camera-title"
            >
                <div className="camera-modal-header">
                    <div>
                        <h2 id="add-camera-title">
                            Thêm camera
                        </h2>

                        <p>
                            Nhập thông tin camera để kết nối với phòng học.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="camera-modal-close"
                        onClick={onClose}
                        aria-label="Đóng"
                    >
                        <Icon
                            name="close"
                            size={19}
                        />
                    </button>
                </div>

                <form
                    className="camera-form"
                    onSubmit={handleSubmit}
                >
                    <div className="camera-form-grid">
                        <div className="camera-form-field">
                            <label htmlFor="room_id">
                                Mã phòng
                                <span>*</span>
                            </label>

                            <input
                                id="room_id"
                                name="room_id"
                                type="text"
                                placeholder="Ví dụ: p201a"
                                required
                            />

                            <small>
                                Mã document của phòng trong classrooms.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="camera_name">
                                Tên camera
                                <span>*</span>
                            </label>

                            <input
                                id="camera_name"
                                name="camera_name"
                                type="text"
                                placeholder="Ví dụ: Camera 201"
                                required
                            />

                            <small>
                                Trùng camera_id trong cấu hình của camera AI.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="ip_address">
                                Địa chỉ IP
                                <span>*</span>
                            </label>

                            <input
                                id="ip_address"
                                name="ip_address"
                                type="text"
                                placeholder="Ví dụ: 192.168.1.103"
                                required
                            />
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="rtsp_port">
                                RTSP Port
                                <span>*</span>
                            </label>

                            <input
                                id="rtsp_port"
                                name="rtsp_port"
                                type="text"
                                placeholder="Ví dụ: 554"
                                required
                            />
                        </div>
                    </div>

                    <div className="camera-form-note">
                        <Icon
                            name="alertCircle"
                            size={17}
                        />

                        <p>
                            Địa chỉ RTSP (kèm tài khoản, mật khẩu của camera) chỉ được cấu hình trên máy camera AI,
                            web không lưu. Tình trạng camera hiển thị khi camera AI gửi tín hiệu.
                        </p>
                    </div>

                    <div className="camera-modal-actions">
                        <button
                            type="button"
                            className="camera-cancel-button"
                            onClick={onClose}
                        >
                            Hủy
                        </button>

                        <button
                            type="submit"
                            className="camera-save-button"
                        >
                            <Icon
                                name="plus"
                                size={16}
                            />

                            <span>
                                Thêm camera
                            </span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddCameraForm;
