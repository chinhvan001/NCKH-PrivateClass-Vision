const API_BASE_URL = "http://127.0.0.1:5000";


const getAuthHeaders = () => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    return {
        Authorization: `Bearer ${idToken}`,
    };
};

export const getCameras = async () => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras`,
        {
            method: "GET",
            headers: getAuthHeaders(),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể lấy danh sách camera."
        );
    }

    return data.cameras || [];
};

export const getClassrooms = async () => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/classrooms`,
        {
            method: "GET",
            headers: getAuthHeaders(),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể lấy danh sách phòng học."
        );
    }

    return data.classrooms || [];
};

export const createCamera = async (cameraData) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras`,
        {
            method: "POST",
            headers: {
                ...getAuthHeaders(),
                "Content-Type": "application/json",
            },
            body: JSON.stringify(cameraData),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể thêm camera."
        );
    }

    return data;
};

export const updateCamera = async (cameraId, cameraData) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${encodeURIComponent(cameraId)}`,
        {
            method: "PUT",
            headers: {
                ...getAuthHeaders(),
                "Content-Type": "application/json",
            },
            body: JSON.stringify(cameraData),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể lưu camera."
        );
    }

    return data;
};

// Ảnh camera để test (backend bật CAMERA_SNAPSHOT=1): object URL trong bộ nhớ trình duyệt, không lưu ở đâu.
// Người gọi thu hồi bằng URL.revokeObjectURL khi không dùng nữa.
export const getCameraSnapshot = async (cameraId) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${encodeURIComponent(cameraId)}/snapshot`,
        {
            method: "GET",
            headers: getAuthHeaders(),
            cache: "no-store",
        }
    );

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));

        throw new Error(
            data.message ||
            "Không lấy được hình từ camera."
        );
    }

    return URL.createObjectURL(await response.blob());
};

export const deleteCamera = async (cameraId) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${encodeURIComponent(cameraId)}`,
        {
            method: "DELETE",
            headers: getAuthHeaders(),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể xóa camera."
        );
    }

    return data;
};