"""Test output preview da duoc an danh, khong phu thuoc model that."""

import numpy as np

from src.privacy import anonymize_preview, blur_regions


def test_blur_regions_changes_non_uniform_face_area():
    image = np.zeros((80, 80, 3), dtype=np.uint8)
    pattern = np.repeat(np.arange(40, dtype=np.uint8)[:, None], 40, axis=1)
    image[20:60, 20:60] = pattern[:, :, None]
    before = image.copy()

    blur_regions(image, [(20, 20, 40, 40)])

    assert not np.array_equal(image, before)


def test_anonymize_preview_pixelates_entire_frame_for_undetected_faces_too():
    image = np.arange(96 * 96 * 3, dtype=np.uint8).reshape(96, 96, 3)
    before = image.copy()

    anonymize_preview(image)

    assert not np.array_equal(image, before)
    # Pixelation: trong mot block 3x4, mau phai dong nhat theo nearest-neighbor.
    assert np.all(image[0:4, 0:3] == image[0, 0])
