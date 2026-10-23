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

export const testCameraConnection = async (rtspUrl) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/test-connection`,
        {
            method: "POST",
            headers: {
                ...getAuthHeaders(),
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                rtsp_url: rtspUrl,
            }),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể kiểm tra kết nối camera."
        );
    }

    return data;
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

export const configureCamera = async (cameraId) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${cameraId}/configure`,
        {
            method: "PUT",
            headers: getAuthHeaders(),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể kiểm tra camera."
        );
    }

    return data;
};

export const deleteCamera = async (cameraId) => {
    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${cameraId}`,
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