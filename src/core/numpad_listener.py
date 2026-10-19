"""Düşük seviyeli klavye ve numpad dinleyici modülü.

Windows kanca API'si (WH_KEYBOARD_LL) kullanarak Numpad Enter tuşunu
ve çift basma olaylarını 64-bit uyumlu Win32 çağrılarıyla dinler.
"""

import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Optional
from src.core.double_tap_detector import DoubleTapDetector
from src.utils.logger import get_logger

logger = get_logger()

# Windows Hook ve Tuş Sabitleri
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012
VK_RETURN = 0x0D
LLKHF_EXTENDED = 0x0001


class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Win32 KBDLLHOOKSTRUCT yapısı (64-bit uyumlu)."""
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


# Kanca geri çağırma prototipi (64-bit LRESULT dönüşü)
HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
)

# Win32 API Tiplerini Yapılandır
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

kernel32.GetLastError.restype = wintypes.DWORD

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    HOOKPROC,
    wintypes.HINSTANCE,
    wintypes.DWORD
]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM
]
user32.CallNextHookEx.restype = ctypes.c_longlong

user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT
]
user32.GetMessageW.restype = wintypes.BOOL

user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = ctypes.c_longlong

user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
]
user32.PostThreadMessageW.restype = wintypes.BOOL


class NumpadListener:
    """Numpad Enter çift basımını dinleyen servis sınıfı."""

    def __init__(
        self,
        on_double_tap: Callable[[], None],
        threshold_ms: int = 400,
        allow_standard_enter: bool = True
    ) -> None:
        """NumpadListener sınıfını başlatır.

        Args:
            on_double_tap: Çift basım olduğunda çalıştırılacak fonksiyon.
            threshold_ms: Çift basım kabul edilecek milisaniye süresi.
            allow_standard_enter: True ise normal Enter tuşunun çift basımını da kabul eder.
        """
        self.on_double_tap = on_double_tap
        self.allow_standard_enter = allow_standard_enter
        self.detector = DoubleTapDetector(
            threshold_ms=threshold_ms,
            on_double_tap=self._handle_double_tap
        )

        self._hook_id: Optional[int] = None
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._is_running = False
        self._hook_proc_ref: Optional[HOOKPROC] = None

    def _handle_double_tap(self, key_id: str) -> None:
        """Dedektörden gelen çift basma sinyalini ana işleyiciye iletir."""
        logger.info("Numpad tetikleyici aktive oldu (%s)!", key_id)
        try:
            self.on_double_tap()
        except Exception as e:
            logger.error("Tetikleyici çalıştırılırken hata: %s", e)

    def _low_level_handler(self, n_code: int, w_param: int, l_param: int) -> int:
        """Düşük seviyeli kanca geri çağırma fonksiyonu."""
        if n_code >= 0 and (w_param == WM_KEYDOWN or w_param == WM_SYSKEYDOWN):
            try:
                kb_struct = KBDLLHOOKSTRUCT.from_address(l_param)
                vk = kb_struct.vkCode
                flags = kb_struct.flags

                if vk == VK_RETURN:
                    is_numpad = bool(flags & LLKHF_EXTENDED)
                    key_id = "numpad_enter" if is_numpad else "standard_enter"
                    logger.debug(
                        "Enter basıldı: vk=%d, scan=%d, flags=%d, is_numpad=%s",
                        vk, kb_struct.scanCode, flags, is_numpad
                    )

                    effective_id = "enter" if self.allow_standard_enter else key_id
                    if is_numpad or self.allow_standard_enter:
                        self.detector.register_press(effective_id)
            except Exception as e:
                logger.error("Kanca işleme hatası: %s", e)

        return user32.CallNextHookEx(self._hook_id, n_code, w_param, l_param)

    def _run_loop(self) -> None:
        """Kanca döngüsünü arka plan iş parçacığında çalıştırır."""
        self._thread_id = threading.get_native_id()
        self._hook_proc_ref = HOOKPROC(self._low_level_handler)

        h_mod = kernel32.GetModuleHandleW(None)

        # 64-bit güvenli kanca oluşturma
        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc_ref,
            h_mod,
            0
        )

        # Alternatif: h_mod None denenir
        if not self._hook_id:
            err = kernel32.GetLastError()
            logger.warning("h_mod ile kanca başarısız oldu (Hata: %d), None deneniyor...", err)
            self._hook_id = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                self._hook_proc_ref,
                None,
                0
            )

        if not self._hook_id:
            err = kernel32.GetLastError()
            logger.error("SetWindowsHookExW tamamen başarısız oldu! Win32 Hata Kodu: %d", err)
            self._is_running = False
            return

        logger.info("Klavye kancası başarıyla kuruldu (Hook Handle: %s). Dinleme aktif.", self._hook_id)
        self._is_running = True

        # Windows Mesaj Döngüsü
        msg = wintypes.MSG()
        while self._is_running:
            b_ret = user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            if b_ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None
            logger.info("Klavye kancası kaldırıldı.")

    def start(self) -> None:
        """Dinleyiciyi arka planda başlatır."""
        if self._is_running:
            logger.warning("Dinleyici zaten çalışıyor.")
            return

        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="NumpadHookThread")
        self._thread.start()
        logger.info("Dinleyici arka plan iş parçacığı başlatıldı.")

    def stop(self) -> None:
        """Dinleyiciyi durdurur."""
        self._is_running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("Dinleyici durduruldu.")
