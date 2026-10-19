"""Yapılandırma yönetim modülü.

Uygulama ayarlarını ve numpad sayı-aksiyon eşleştirmelerini yönetir.
Tek Doğruluk Kaynağı (SSOT) prensibini uygular.
"""

import json
import os
from typing import Any, Dict, List, Optional
from src.utils.logger import get_logger

logger = get_logger()

DEFAULT_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "hotkey": {
        "key_type": "numpad_enter",
        "double_tap_threshold_ms": 400,
        "allow_standard_enter": True
    },
    "ui": {
        "width": 640,
        "height": 72,
        "expanded_height": 380,
        "auto_execute_delay_sec": 5,
        "theme": {
            "bg_color": "#181825",
            "border_color": "#313244",
            "input_bg": "#1e1e2e",
            "text_color": "#cdd6f4",
            "placeholder_color": "#6c7086",
            "accent_color": "#89b4fa",
            "selected_bg": "#45475a"
        }
    },
    "actions": [
        {
            "code": "1",
            "title": "Hesap Makinesi",
            "description": "Windows Hesap Makinesi uygulamasını açar.",
            "type": "cmd",
            "command": "calc.exe"
        },
        {
            "code": "2",
            "title": "Not Defteri",
            "description": "Hızlı not almak için Notepad açar.",
            "type": "cmd",
            "command": "notepad.exe"
        },
        {
            "code": "3",
            "title": "Görev Yöneticisi",
            "description": "Windows Görev Yöneticisini başlatır.",
            "type": "cmd",
            "command": "taskmgr.exe"
        },
        {
            "code": "4",
            "title": "Tarayıcı - Google",
            "description": "Varsayılan tarayıcıda Google ana sayfasını açar.",
            "type": "url",
            "command": "https://www.google.com"
        },
        {
            "code": "5",
            "title": "Terminal (PowerShell)",
            "description": "Windows PowerShell penceresi açar.",
            "type": "cmd",
            "command": "powershell.exe"
        },
        {
            "code": "0",
            "title": "Ekranı Kilitle",
            "description": "Oturumu güvenli bir şekilde kilitler.",
            "type": "cmd",
            "command": "rundll32.exe user32.dll,LockWorkStation"
        }
    ]
}


class ConfigManager:
    """Yapılandırma verilerini yükleyen, doğrulayan ve saklayan sınıf."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """ConfigManager sınıfını başlatır.

        Args:
            config_path: Özel yapılandırma dosyası yolu. Belirtilmezse varsayılan kullanılır.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Yapılandırma dosyasını diskten yükler veya varsayılanı oluşturur.

        Returns:
            Dict[str, Any]: Yüklenen yapılandırma verisi.
        """
        if not os.path.exists(self.config_path):
            logger.info("Yapılandırma dosyası bulunamadı. Varsayılan oluşturuluyor: %s", self.config_path)
            self._data = dict(DEFAULT_CONFIG)
            self.save()
            return self._data

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self._data = self._merge_defaults(loaded, DEFAULT_CONFIG)
                logger.debug("Yapılandırma başarıyla yüklendi: %s", self.config_path)
        except Exception as e:
            logger.error("Yapılandırma okunurken hata oluştu: %s. Varsayılanlar yüklendi.", e)
            self._data = dict(DEFAULT_CONFIG)

        return self._data

    def save(self) -> bool:
        """Mevcut yapılandırmayı diske yazar.

        Returns:
            bool: İşlem başarılı ise True.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
            logger.debug("Yapılandırma diske kaydedildi: %s", self.config_path)
            return True
        except Exception as e:
            logger.error("Yapılandırma kaydedilirken hata oluştu: %s", e)
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Belirtilen anahtara ait değeri döndürür."""
        return self._data.get(key, default)

    def get_actions(self) -> List[Dict[str, Any]]:
        """Kayıtlı eylem listesini döndürür."""
        return self._data.get("actions", [])

    def get_action_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Sayı koduna göre ilgili eylemi bulur.

        Args:
            code: Eyleme ait sayı kodu (örn: '1', '42').

        Returns:
            Optional[Dict[str, Any]]: Eşleşen eylem veya None.
        """
        code_str = str(code).strip()
        for action in self.get_actions():
            if str(action.get("code", "")).strip() == code_str:
                return action
        return None

    def _merge_defaults(self, custom: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Eksik anahtarları varsayılanlarla doldurur (Kalıtım ve SSOT)."""
        result = dict(defaults)
        for k, v in custom.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = self._merge_defaults(v, result[k])
            else:
                result[k] = v
        return result
