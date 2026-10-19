"""ConfigManager birim testleri."""

import os
import tempfile
import unittest
from src.config.config_manager import ConfigManager, DEFAULT_CONFIG


class TestConfigManager(unittest.TestCase):
    """Yapılandırma yöneticisi testleri."""

    def test_default_config_creation(self):
        """Dosya yoksa varsayılan yapılandırma oluşturulmalıdır."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            self.assertTrue(os.path.exists(temp_config))
            self.assertEqual(manager.get("version"), "1.0.0")
            self.assertTrue(len(manager.get_actions()) > 0)

    def test_get_action_by_code(self):
        """Koda göre eylem doğru getirilmelidir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            action = manager.get_action_by_code("1")
            self.assertIsNotNone(action)
            self.assertEqual(action.get("code"), "1")
            self.assertEqual(action.get("command"), "calc.exe")

    def test_unknown_action_code_returns_none(self):
        """Bilinmeyen kod None dönmelidir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            action = manager.get_action_by_code("non_existent_code")
            self.assertIsNone(action)

    def test_auto_execute_delay_sec_setting(self):
        """Otomatik çalıştırma gecikmesi 5 saniye olarak yapılandırılmış olmalıdır."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            ui_config = manager.get("ui", {})
            self.assertEqual(ui_config.get("auto_execute_delay_sec"), 5)


if __name__ == "__main__":
    unittest.main()
