"""Tao preview/debug da an danh; khong dung cho inference."""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import cv2


def blur_regions(image, regions: Iterable[Tuple[int, int, int, int]]) -> None:
    """Lam mo cac vung ``(x, y, width, height)`` trong anh theo best-effort."""
    height, width = image.shape[:2]
    for x, y, region_width, region_height in regions:
        left, top = max(0, x), max(0, y)
        right, bottom = min(width, x + region_width), min(height, y + region_height)
        if right - left < 2 or bottom - top < 2:
            continue
        roi = image[top:bottom, left:right]
        kernel = max(15, (min(right - left, bottom - top) // 2) * 2 + 1)
        kernel = min(kernel, 99)
        roi[:] = cv2.GaussianBlur(roi, (kernel, kernel), 0)


def face_regions_from_poses(people: Sequence[object]) -> list[Tuple[int, int, int, int]]:
    """Uoc luong vung mat tu 5 keypoint dau cua COCO-pose.

    Vung fallback o phan tren bbox bao phu ca truong hop mat bi mat keypoint.
    """
    regions = []
    for person in people:
        bbox = person.bbox
        x1, y1, x2, y2 = (int(value) for value in bbox)
        head_height = max(24, int((y2 - y1) * 0.35))
        points = [point for point in person.keypoints[:5] if point[2] >= 0.2]
        if points:
            min_x = min(point[0] for point in points)
            max_x = max(point[0] for point in points)
            min_y = min(point[1] for point in points)
            max_y = max(point[1] for point in points)
            padding = max(12, int(max(max_x - min_x, max_y - min_y) * 1.5))
            regions.append(
                (
                    int(min_x - padding),
                    int(min_y - padding),
                    int(max_x - min_x + 2 * padding),
                    int(max_y - min_y + 2 * padding),
                )
            )
        else:
            regions.append((x1, y1, max(1, x2 - x1), head_height))
    return regions


def anonymize_preview(image, people: Sequence[object] = ()) -> None:
    """An danh moi preview/debug bang blur mat va pixelate toan khung.

    Pixelate toan khung la fallback bat buoc cho nguoi khong duoc pose detector
    bat ra; do do khong co khuon mat bi bo sot trong output debug.
    """
    blur_regions(image, face_regions_from_poses(people))
    height, width = image.shape[:2]
    # 32 pixel blocks theo chieu rong/cao du nho de khuon mat khong con chi tiet.
    small_width = min(32, width)
    small_height = min(24, height)
    pixelated = cv2.resize(image, (small_width, small_height), interpolation=cv2.INTER_AREA)
    image[:] = cv2.resize(pixelated, (width, height), interpolation=cv2.INTER_NEAREST)
