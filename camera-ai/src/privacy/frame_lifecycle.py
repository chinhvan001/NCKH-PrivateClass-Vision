"""Quan ly vong doi ngan cua frame trong RAM.

Khong ham nay nao ghi frame ra dia. ``wipe_image`` ghi de mang pixel co the
ghi duoc truoc khi bo reference; day la best-effort trong Python/OpenCV, khong
phai bao dam xoa sach bo nho vat ly cua runtime hay GPU.
"""

from typing import Any


def wipe_image(image: Any) -> None:
    """Ghi 0 de xoa noi dung pixel trong RAM neu buffer cho phep ghi."""
    if image is None:
        return
    try:
        if getattr(image, "flags", None) is not None and not image.flags.writeable:
            return
        image.fill(0)
    except (AttributeError, TypeError, ValueError):
        # Frame gia lap trong unit test hay buffer read-only khong co pixel
        # ghi de duoc. Van bo reference o caller.
        return


def dispose_frame(frame: Any) -> None:
    """Xoa pixel cua ``frame.image`` theo best-effort roi bo reference o caller."""
    wipe_image(getattr(frame, "image", None))
