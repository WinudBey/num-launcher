"""LineCounter birim testleri."""

import os
import unittest
from src.utils.line_counter import count_file_lines, scan_directory_lines, MAX_LINE_LIMIT


class TestLineCounter(unittest.TestCase):
    """Satır sayısı denetleyici testleri."""

    def test_count_file_lines(self):
        """Mevcut dosyanın satır sayısı 0'dan büyük olmalıdır."""
        lines = count_file_lines(__file__)
        self.assertGreater(lines, 0)
        self.assertLess(lines, MAX_LINE_LIMIT)

    def test_scan_directory_lines(self):
        """Proje dosyaları 1000 satır sınırını aşmamalıdır."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        is_valid, violations, _ = scan_directory_lines(project_root, max_limit=MAX_LINE_LIMIT)

        self.assertTrue(is_valid, f"Satır sınırı ihlalleri: {violations}")
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
