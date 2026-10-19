"""ActionRegistry birim testleri."""

import unittest
from src.core.action_registry import ActionRegistry, ActionExecutionResult


class TestActionRegistry(unittest.TestCase):
    """Eylem yürütme ve eşleştirme testleri."""

    def setUp(self):
        self.sample_actions = [
            {"code": "1", "title": "Hesap Makinesi", "description": "calc", "type": "cmd", "command": "calc.exe"},
            {"code": "11", "title": "Tarayıcı", "description": "web", "type": "url", "command": "https://example.com"},
            {"code": "2", "title": "Not Defteri", "description": "notepad", "type": "cmd", "command": "notepad.exe"},
        ]
        self.registry = ActionRegistry(self.sample_actions)

    def test_filter_exact_match(self):
        """Koda göre tam eşleşme en başta yer almalıdır."""
        matches = self.registry.filter_actions("1")
        self.assertTrue(len(matches) >= 2)
        self.assertEqual(matches[0]["code"], "1")
        self.assertEqual(matches[1]["code"], "11")

    def test_filter_text_search(self):
        """Başlık ve açıklama araması doğru sonuç vermelidir."""
        matches = self.registry.filter_actions("not")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["code"], "2")

    def test_custom_handler_execution(self):
        """Özel işleyici başarıyla tetiklenmelidir."""
        executed = []
        self.registry.register_custom_handler(
            "custom_mock",
            lambda act: executed.append(act["code"])
        )

        custom_action = {
            "code": "99",
            "title": "Mock Eylem",
            "type": "custom_mock",
            "command": ""
        }
        res = self.registry.execute_action(custom_action)

        self.assertTrue(res.success)
        self.assertEqual(executed, ["99"])

    def test_unknown_code_execution(self):
        """Tanımsız kod çalıştırıldığında hata dönmelidir."""
        res = self.registry.execute_by_code("99999")
        self.assertFalse(res.success)


if __name__ == "__main__":
    unittest.main()
