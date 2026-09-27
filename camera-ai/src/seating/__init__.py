"""
Module seating/ -- Pseudonymous Spatial Seating Mapping: gan skeleton (tu
module detection/) vao seat_id dua tren vi tri khong gian, KHONG dung bat ky
hinh thuc nhan dien danh tinh nao (dung tinh than Proposal chinh thuc).

seat_grid.py: dinh nghia luoi cho ngoi + doc file calibration cuc bo.
seat_mapper.py: gan tung khung hinh doc lap (nearest-centroid).
Theo doi on dinh qua nhieu khung hinh (tracking) la phan viec tiep theo
(task 3.4), chua co trong module nay.
"""

from .seat_grid import Seat, SeatGrid, SeatGridError
from .seat_mapper import SeatAssignment, assign_seats, shoulder_midpoint
from .seat_tracker import SeatTracker

__all__ = [
    "Seat",
    "SeatGrid",
    "SeatGridError",
    "SeatAssignment",
    "assign_seats",
    "shoulder_midpoint",
    "SeatTracker",
]