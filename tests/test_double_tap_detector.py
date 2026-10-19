"""DoubleTapDetector birim testleri."""

import unittest
from src.core.double_tap_detector import DoubleTapDetector


class TestDoubleTapDetector(unittest.TestCase):
    """Çift basma algılayıcı test sınıfı."""

    def test_single_press_does_not_trigger(self):
        """Tek basımda çift basma tetiklenmemelidir."""
        triggered = []
        detector = DoubleTapDetector(threshold_ms=400, on_double_tap=lambda k: triggered.append(k))

        res = detector.register_press("numpad_enter", current_time=100.0)
        self.assertFalse(res)
        self.assertEqual(len(triggered), 0)

    def test_double_press_within_threshold_triggers(self):
        """Eşik içinde iki basım yapıldığında tetiklenmelidir."""
        triggered = []
        detector = DoubleTapDetector(threshold_ms=400, on_double_tap=lambda k: triggered.append(k))

        detector.register_press("numpad_enter", current_time=100.0)
        res = detector.register_press("numpad_enter", current_time=100.25)  # 250 ms sonra

        self.assertTrue(res)
        self.assertEqual(triggered, ["numpad_enter"])

    def test_slow_press_does_not_trigger(self):
        """Eşik aşıldığında çift basma sayılmamalıdır."""
        triggered = []
        detector = DoubleTapDetector(threshold_ms=400, on_double_tap=lambda k: triggered.append(k))

        detector.register_press("numpad_enter", current_time=100.0)
        res = detector.register_press("numpad_enter", current_time=100.5)  # 500 ms sonra

        self.assertFalse(res)
        self.assertEqual(len(triggered), 0)

    def test_third_press_does_not_trigger_again_immediately(self):
        """İkili basım sonrası üçüncü basım tekil basım gibi davranmalıdır."""
        triggered = []
        detector = DoubleTapDetector(threshold_ms=400, on_double_tap=lambda k: triggered.append(k))

        # 1. ve 2. basım -> çift basım
        detector.register_press("numpad_enter", current_time=100.0)
        res2 = detector.register_press("numpad_enter", current_time=100.2)
        self.assertTrue(res2)

        # 3. basım -> yeni döngünün ilk basımı olmalı
        res3 = detector.register_press("numpad_enter", current_time=100.3)
        self.assertFalse(res3)

        # 4. basım -> ikinci çift basım
        res4 = detector.register_press("numpad_enter", current_time=100.4)
        self.assertTrue(res4)
        self.assertEqual(len(triggered), 2)


if __name__ == "__main__":
    unittest.main()
