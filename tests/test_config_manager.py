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

    def test_add_and_validate_action(self):
        """Yeni eylem ekleme ve geçerlilik denetimi çalışmalıdır."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            initial_count = len(manager.get_actions())
            new_action = {
                "code": "9",
                "title": "VS Code",
                "description": "Visual Studio Code açar.",
                "type": "cmd",
                "command": "code"
            }
            res = manager.add_action(new_action)
            self.assertTrue(res)
            self.assertEqual(len(manager.get_actions()), initial_count + 1)
            self.assertEqual(manager.get_action_by_code("9")["title"], "VS Code")

            # Geçersiz eylem testi
            invalid_action = {"code": "", "type": "unknown"}
            self.assertFalse(manager.add_action(invalid_action))

    def test_update_and_delete_action(self):
        """Eylem güncelleme ve silme çalışmalıdır."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            # İlk elemanı güncelle
            updated_data = {
                "code": "11",
                "title": "Gelişmiş Hesap Makinesi",
                "description": "calc güncellendi",
                "type": "cmd",
                "command": "calc.exe"
            }
            res = manager.update_action(0, updated_data)
            self.assertTrue(res)
            self.assertEqual(manager.get_actions()[0]["code"], "11")

            # İlk elemanı sil
            count_before = len(manager.get_actions())
            del_res = manager.delete_action(0)
            self.assertTrue(del_res)
            self.assertEqual(len(manager.get_actions()), count_before - 1)

    def test_move_action_order(self):
        """Eylemlerin sırası doğru değiştirilmelidir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config = os.path.join(temp_dir, "config.json")
            manager = ConfigManager(temp_config)

            first_code = manager.get_actions()[0]["code"]
            second_code = manager.get_actions()[1]["code"]

            # İlk elemanı ikinci sıraya taşı (0 -> 1)
            res = manager.move_action(0, 1)
            self.assertTrue(res)
            self.assertEqual(manager.get_actions()[0]["code"], second_code)
            self.assertEqual(manager.get_actions()[1]["code"], first_code)


if __name__ == "__main__":
    unittest.main()

