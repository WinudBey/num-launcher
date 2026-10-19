"""DisplayDetector birim testleri."""

import unittest
from src.core.display_detector import (
    DisplayArea,
    calculate_centered_window_position,
    get_cursor_position,
    get_monitor_for_cursor
)


class TestDisplayDetector(unittest.TestCase):
    """Monitör ve fare algılama testleri."""

    def test_cursor_position_returns_integers(self):
        """İmleç konumu int türünde x, y döndürmelidir."""
        pos = get_cursor_position()
        self.assertIsInstance(pos, tuple)
        self.assertEqual(len(pos), 2)
        self.assertIsInstance(pos[0], int)
        self.assertIsInstance(pos[1], int)

    def test_monitor_for_cursor_returns_valid_dimensions(self):
        """Monitör çalışma alanı pozitif genişlik ve yükseklik döndürmelidir."""
        area = get_monitor_for_cursor()
        self.assertIsInstance(area, DisplayArea)
        self.assertGreater(area.width, 0)
        self.assertGreater(area.height, 0)

    def test_calculate_centered_window_position(self):
        """Pencere yatayda ortalanmış koordinatta olmalıdır."""
        win_w, win_h = 600, 80
        pos = calculate_centered_window_position(win_w, win_h, cursor_pos=(500, 500))
        area = get_monitor_for_cursor(cursor_pos=(500, 500))

        expected_x = area.left + (area.width - win_w) // 2
        self.assertEqual(pos.x, expected_x)
        self.assertEqual(pos.width, win_w)
        self.assertEqual(pos.height, win_h)


if __name__ == "__main__":
    unittest.main()
