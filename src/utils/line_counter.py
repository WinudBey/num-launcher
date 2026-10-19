"""Dosya satır sayısı denetleyici modülü.

Bu modül proje dosyalarının 1000 satır sınırını aşıp aşmadığını denetler.
"""

import os
from typing import Dict, List, Tuple

MAX_LINE_LIMIT = 1000
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
ALLOWED_EXTENSIONS = {".py", ".js", ".html", ".css", ".json", ".md"}


def count_file_lines(file_path: str) -> int:
    """Belirtilen dosyadaki toplam satır sayısını sayar.

    Args:
        file_path: İncelenecek dosyanın mutlak veya göreli yolu.

    Returns:
        int: Satır sayısı.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def scan_directory_lines(root_dir: str, max_limit: int = MAX_LINE_LIMIT) -> Tuple[bool, List[str], Dict[str, int]]:
    """Dizindeki tüm uygun kaynak dosyalarını tarar ve sınır kontrolü yapar.

    Args:
        root_dir: Taranacak kök dizin.
        max_limit: İzin verilen azami satır sayısı.

    Returns:
        Tuple[bool, List[str], Dict[str, int]]:
            - Başarılı mı (hiçbir dosya sınırı aşmadı mı).
            - Sınırı aşan dosyaların hata mesajları.
            - Taranan dosya ve satır sayıları sözlüğü.
    """
    violations: List[str] = []
    file_counts: Dict[str, int] = {}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                full_path = os.path.join(root, file_name)
                lines = count_file_lines(full_path)
                rel_path = os.path.relpath(full_path, root_dir)
                file_counts[rel_path] = lines

                if lines > max_limit:
                    violations.append(
                        f"KURAL İHLALİ: {rel_path} ({lines} satır) azami sınırı ({max_limit}) aşıyor!"
                    )

    is_valid = len(violations) == 0
    return is_valid, violations, file_counts
