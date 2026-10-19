"""Çift basma algılayıcı modülü.

Bu modül belirtilen zaman eşiği içinde aynı tuşa iki kez basılmasını tespit eder.
Mantıksal kontrolleri işletim sistemi kancalarından (hook) bağımsız tutar.
"""

import time
from typing import Callable, Dict, Optional
from src.utils.logger import get_logger

logger = get_logger()


class DoubleTapDetector:
    """Tuş çift basma olaylarını takip eden ve tetikleyen sınıf."""

    def __init__(
        self,
        threshold_ms: int = 400,
        on_double_tap: Optional[Callable[[str], None]] = None
    ) -> None:
        """DoubleTapDetector sınıfını başlatır.

        Args:
            threshold_ms: Çift basma kabul edilecek azami milisaniye farkı.
            on_double_tap: Çift basma gerçekleştiğinde çağrılacak geri çağırma fonksiyonu.
        """
        self.threshold_ms = threshold_ms
        self.on_double_tap = on_double_tap
        self._last_press_times: Dict[str, float] = {}

    def register_press(self, key_id: str, current_time: Optional[float] = None) -> bool:
        """Tuş basımını kaydeder ve çift basma durumunu kontrol eder.

        Args:
            key_id: Basılan tuşun kimliği (örn: 'numpad_enter').
            current_time: İşlem zaman damgası (saniye cinsinden float).

        Returns:
            bool: Çift basma tespit edildiyse True, aksi halde False.
        """
        now = current_time if current_time is not None else time.time()
        last_time = self._last_press_times.get(key_id, 0.0)
        elapsed_ms = (now - last_time) * 1000.0

        logger.debug(
            "Tuş basımı: %s | Geçen süre: %.1f ms | Eşik: %d ms",
            key_id, elapsed_ms, self.threshold_ms
        )

        if 0 < elapsed_ms <= self.threshold_ms:
            # Çift basma tespit edildi. Arka arkaya üçüncü basımın yeni çift olmasını engelle.
            self._last_press_times[key_id] = 0.0
            logger.info("Çift basma tespit edildi: %s (%.1f ms)", key_id, elapsed_ms)
            if self.on_double_tap:
                self.on_double_tap(key_id)
            return True

        # İlk basım olarak kaydet
        self._last_press_times[key_id] = now
        return False

    def reset(self, key_id: Optional[str] = None) -> None:
        """Zamanlayıcı geçmişini sıfırlar."""
        if key_id:
            self._last_press_times.pop(key_id, None)
        else:
            self._last_press_times.clear()
