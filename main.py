"""Numpad Bar ana çalıştırma modülü.

Arka planda klavye ve numpad kancasını çalıştırır.
Çift Enter basımı algılandığında fare imlecinin olduğu monitörde
komut çubuğunu açar.
"""

import sys
import threading
from src.config.config_manager import ConfigManager
from src.core.action_registry import ActionRegistry
from src.core.display_detector import get_cursor_position, get_monitor_for_cursor
from src.core.numpad_listener import NumpadListener
from src.ui.overlay_bar import OverlayBar
from src.utils.logger import get_logger, setup_logger

logger = setup_logger(log_to_console=True)


def main() -> None:
    """Uygulamayı başlatır ve ana olay döngüsünü çalıştırır."""
    logger.info("=== Numpad Bar Başlatılıyor ===")

    # 1. Yapılandırmayı yükle
    config_mgr = ConfigManager()
    config = config_mgr.load()

    # 2. Aksiyon motorunu hazırla
    registry = ActionRegistry(config_mgr.get_actions())

    # 3. Arayüz penceresini oluştur (Tkinter ana iş parçacığında çalışır)
    overlay = OverlayBar(
        registry=registry,
        config=config,
        on_action_executed=lambda res: logger.info("Aksiyon tamamlandı: %s", res)
    )

    # 4. Çift basım olduğunda arayüzü ana iş parçacığında güvenle aç
    def trigger_show_bar() -> None:
        pos = get_cursor_position()
        area = get_monitor_for_cursor(pos)
        logger.info(
            "Tetikleme alındı! Fare konumu: %s | Monitör alanı: [sol=%d, üst=%d, w=%d, h=%d]",
            pos, area.left, area.top, area.width, area.height
        )
        if overlay.root:
            overlay.root.after(0, overlay.show)

    # 5. Numpad dinleyicisini başlat
    hotkey_cfg = config.get("hotkey", {})
    threshold_ms = int(hotkey_cfg.get("double_tap_threshold_ms", 400))
    allow_std = bool(hotkey_cfg.get("allow_standard_enter", True))

    listener = NumpadListener(
        on_double_tap=trigger_show_bar,
        threshold_ms=threshold_ms,
        allow_standard_enter=allow_std
    )
    listener.start()

    logger.info("Numpad Bar hazır! Numpad Enter'a iki kez hızlıca basabilirsiniz.")
    logger.info("Kapatmak için konsolda Ctrl+C tuşlayın veya pencereyi kapatın.")

    try:
        if overlay.root:
            overlay.root.mainloop()
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu.")
    finally:
        listener.stop()
        logger.info("Numpad Bar güvenle kapatıldı.")


if __name__ == "__main__":
    main()
