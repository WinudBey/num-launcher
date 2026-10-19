"""Bütünleşik Proje Doğrulama Modülü (verify.py).

Bu script tek komutla:
1. Kaynak dosyaların satır sayısı sınırını (< 1000 satır) denetler.
2. Birim testleri (unit tests) çalıştırır.
3. Playwright uçtan uca görsel testleri yürütür.
"""

import os
import subprocess
import sys
from src.utils.line_counter import MAX_LINE_LIMIT, scan_directory_lines


def print_header(title: str) -> None:
    """Başlık satırını ekrana yazar."""
    print("\n" + "=" * 65)
    print(f" >>> {title}")
    print("=" * 65)


def check_line_limits(root_dir: str) -> bool:
    """Tüm kaynak dosyalarının 1000 satır sınırını kontrol eder."""
    print_header("ADIM 1: Satır Sayısı Denetimi (Azami 1000 Satır)")
    is_valid, violations, file_counts = scan_directory_lines(root_dir, max_limit=MAX_LINE_LIMIT)

    print(f"Toplam taranan dosya sayısı: {len(file_counts)}")
    for f_path, count in sorted(file_counts.items()):
        status = "UYGUN" if count <= MAX_LINE_LIMIT else "AŞILDI!"
        print(f" - {f_path:<45} : {count:>4} satır [{status}]")

    if not is_valid:
        print("\n[HATA] Satır sınırı ihlalleri tespit edildi:")
        for v in violations:
            print(f" ! {v}")
        return False

    print("\n[BAŞARILI] Tüm dosyalar 1000 satır sınırına uygundur.")
    return True


def run_unit_tests() -> bool:
    """Python birim testlerini çalıştırır."""
    print_header("ADIM 2: Birim Testleri (Unit Tests)")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n[BAŞARILI] Tüm birim testleri başarıyla geçti.")
        return True
    print("\n[HATA] Birim testlerinde hata oluştu!")
    return False


def run_playwright_tests() -> bool:
    """Playwright E2E ve görsel testlerini çalıştırır."""
    print_header("ADIM 3: Playwright Uçtan Uca ve Görsel Testler")
    # Windows üzerinde npx.cmd
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    cmd = [npx_cmd, "playwright", "test"]
    try:
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print("\n[BAŞARILI] Tüm Playwright testleri ve görsel doğrulamalar geçti.")
            return True
        print("\n[HATA] Playwright testleri başarısız oldu!")
        return False
    except Exception as e:
        print(f"\n[HATA] Playwright çalıştırılırken istisna: {e}")
        return False


def main() -> None:
    """Tüm doğrulama adımlarını sıralı olarak yürütür."""
    root_dir = os.path.abspath(os.path.dirname(__file__))
    print(">>> Numpad Bar Bütünleşik Doğrulama Başlatıldı <<<")

    step1 = check_line_limits(root_dir)
    step2 = run_unit_tests()
    step3 = run_playwright_tests()

    print_header("DOĞRULAMA ÖZETİ")
    print(f"1. Satır Sınırı Denetimi : {'GEÇTİ' if step1 else 'BAŞARISIZ'}")
    print(f"2. Birim Testleri         : {'GEÇTİ' if step2 else 'BAŞARISIZ'}")
    print(f"3. Playwright E2E Testleri: {'GEÇTİ' if step3 else 'BAŞARISIZ'}")
    print("=" * 65)

    if step1 and step2 and step3:
        print("\n>>> TEBRİKLER: TÜM TESTLER VE DENETİMLER BAŞARIYLA TAMAMLANDI! <<<\n")
        sys.exit(0)
    else:
        print("\n>>> DİKKAT: BAZI DOĞRULAMA ADIMLARI BAŞARISIZ OLDU! <<<\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
