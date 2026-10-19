"""Türkçe açıklamalı Git commit ve push yardımcısı.

Yapılan değişiklikleri kontrol eder, Türkçe açıklama ile commit oluşturur
ve GitHub master dalına gönderir. İsteğe bağlı olarak sürüm etiketi ekler.
"""

import argparse
import subprocess
import sys


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Komutu çalıştırır ve çıktısını döndürür.

    Args:
        cmd: Çalıştırılacak komut listesi.

    Returns:
        subprocess.CompletedProcess: Komut çalışma sonucu.
    """
    print(f"-> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr:
            print(f"Hata: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def main() -> None:
    """Ana çalıştırma fonksiyonu."""
    parser = argparse.ArgumentParser(
        description="Num Launcher Türkçe Git Push ve Release Aracı"
    )
    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="Türkçe commit açıklaması (örn: 'feat: yeni kısayol eklendi')"
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Otomatik release tetikleyecek sürüm etiketi (örn: v1.0.1)"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Push öncesi verify.py kontrolünü atla"
    )

    args = parser.parse_args()

    message = args.message
    if not message:
        print("Lütfen bir Türkçe commit açıklaması girin:")
        message = input("> ").strip()

    if not message:
        print("Hata: Açıklama boş olamaz.", file=sys.stderr)
        sys.exit(1)

    # Doğrulama adımı
    if not args.no_verify:
        print("Bütünleşik testler ve satır kontrolü yürütülüyor...")
        run_cmd([sys.executable, "verify.py"])

    # Git işlemleri
    print("Değişiklikler ekleniyor...")
    run_cmd(["git", "add", "-A"])

    print(f"Commit oluşturuluyor: '{message}'...")
    # Değişiklik yoksa hata vermesini önle
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip() and not args.tag:
        print("Değişiklik bulunamadı. Commit atlanıyor.")
    else:
        if status.stdout.strip():
            run_cmd(["git", "commit", "-m", message])

    print("GitHub 'master' dalına pushlanıyor...")
    run_cmd(["git", "push", "origin", "master"])

    if args.tag:
        tag_name = args.tag
        if not tag_name.startswith("v"):
            tag_name = f"v{tag_name}"
        print(f"Sürüm etiketi oluşturuluyor: {tag_name}...")
        run_cmd(["git", "tag", "-a", tag_name, "-m", message])
        print(f"Etiket GitHub'a gönderiliyor (Release tetikleniyor): {tag_name}...")
        run_cmd(["git", "push", "origin", tag_name])

    print("\n[BAŞARILI] Tüm değişiklikler GitHub'a aktarıldı.")


if __name__ == "__main__":
    main()
