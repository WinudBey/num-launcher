"""Monitör ve fare konumu algılama modülü.

Bu modül Windows API çağrıları ile fare imlecinin bulunduğu monitörü
ve çalışma alanını (work area) hesaplar.
"""

import ctypes
from ctypes import wintypes
from typing import NamedTuple, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger()

MONITOR_DEFAULTTONEAREST = 2


class DisplayArea(NamedTuple):
    """Monitör çalışma alanı koordinatları."""
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        """Çalışma alanı genişliği."""
        return self.right - self.left

    @property
    def height(self) -> int:
        """Çalışma alanı yüksekliği."""
        return self.bottom - self.top


class WindowPosition(NamedTuple):
    """Hesaplanan pencere koordinatları."""
    x: int
    y: int
    width: int
    height: int


class POINT(ctypes.Structure):
    """Win32 POINT yapısı."""
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(ctypes.Structure):
    """Win32 RECT yapısı."""
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]


class MONITORINFO(ctypes.Structure):
    """Win32 MONITORINFO yapısı."""
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD)
    ]


user32 = ctypes.windll.user32
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.MonitorFromPoint.argtypes = [POINT, wintypes.DWORD]
user32.MonitorFromPoint.restype = wintypes.HMONITOR

user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = wintypes.BOOL


def get_cursor_position() -> Tuple[int, int]:
    """Fare imlecinin mevcut (x, y) piksel koordinatlarını döndürür.

    Returns:
        Tuple[int, int]: Fare imleç koordinatları.
    """
    try:
        pt = POINT()
        if ctypes.windll.user32.GetCursorPos(ctypes.byref(pt)):
            return (pt.x, pt.y)
    except Exception as e:
        logger.error("Fare konumu alınamadı: %s", e)
    return (0, 0)


def get_monitor_for_cursor(cursor_pos: Optional[Tuple[int, int]] = None) -> DisplayArea:
    """Fare imlecinin bulunduğu monitörün çalışma alanını döndürür.

    Args:
        cursor_pos: İsteğe bağlı (x, y) koordinatı. Verilmezse anlık fare konumu alınır.

    Returns:
        DisplayArea: Monitörün çalışma alanı (sol, üst, sağ, alt).
    """
    if cursor_pos is None:
        cursor_pos = get_cursor_position()

    try:
        pt = POINT(cursor_pos[0], cursor_pos[1])
        h_monitor = ctypes.windll.user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)
        if h_monitor:
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(h_monitor, ctypes.byref(mi)):
                work = mi.rcWork
                area = DisplayArea(
                    left=work.left,
                    top=work.top,
                    right=work.right,
                    bottom=work.bottom
                )
                logger.debug(
                    "Monitör bulundu: sol=%d, üst=%d, genişlik=%d, yükseklik=%d",
                    area.left, area.top, area.width, area.height
                )
                return area
    except Exception as e:
        logger.error("Monitör bilgisi alınamadı: %s", e)

    # Hata durumunda varsayılan 1920x1080 ekran alanı
    return DisplayArea(left=0, top=0, right=1920, bottom=1080)


def calculate_centered_window_position(
    window_width: int,
    window_height: int,
    cursor_pos: Optional[Tuple[int, int]] = None,
    top_ratio: float = 0.28
) -> WindowPosition:
    """Belirtilen monitörde pencereyi yatayda ortalayan, dikeyde üst alana yerleştiren koordinatı hesaplar.

    Args:
        window_width: Pencere genişliği.
        window_height: Pencere yüksekliği.
        cursor_pos: Fare konumu. Belirtilmezse anlık fare konumu kullanılır.
        top_ratio: Üstten boşluk oranı (varsayılan: %28).

    Returns:
        WindowPosition: Hesaplanmış (x, y, width, height) değerleri.
    """
    area = get_monitor_for_cursor(cursor_pos)

    # Yatayda tam ortala
    x = area.left + max(0, (area.width - window_width) // 2)

    # Dikeyde üst 1/3 - 1/4 hizasına yerleştir (Raycast / Spotlight standardı)
    y = area.top + int(area.height * top_ratio)

    return WindowPosition(x=x, y=y, width=window_width, height=window_height)
