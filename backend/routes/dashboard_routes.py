from flask import Blueprint, jsonify
from routes.test_helpers import admin_only
from services.dashboard_service import DashboardService

dashboard_bp = admin_only(Blueprint("dashboard_bp", __name__))

@dashboard_bp.route("/api/admin/dashboard-stats", methods=["GET"])
def get_dashboard_stats():
    try:
        data = DashboardService.get_dashboard_summary()
        return jsonify(data), 200
    except Exception as e:
        print("Dashboard API error:", e)
        return jsonify({"success": False, "message": "Không thể tải dữ liệu dashboard."}), 500