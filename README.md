# Num Launcher

Numpad Enter tuşuna iki kez hızlıca basıldığında fare imlecinin bulunduğu monitörde açılan, sayı kodları ile hızlı işlem tetikleyen ve 5 saniye içinde otomatik çalışan modern masaüstü başlatıcı.

---

## Özellikler

- **Numpad Enter Çift Basım Tespiti:** Windows Düşük Seviyeli Klavye Kancası (`WH_KEYBOARD_LL`) ile numpad üzerindeki Enter tuşunu standart Enter tuşundan ayırt eder. 400 milisaniye eşiğinde çift basımı algılar.
- **Monitör Algılama:** Fare imlecinin (`GetCursorPos`) bulunduğu aktif ekranı (`MonitorFromPoint`) ve çalışma alanını tespit eder. Komut çubuğunu doğrudan o monitörün üst-orta alanına yerleştirir.
- **Sayı ve Metin Filtreleme:** Numpad'den girilen sayılara veya arama metnine göre tanımlı aksiyonları anında filtreler.
- **5 Saniye Otomatik Yürütme ve Dolum Animasyonu:** Sayı yazıldığında 5 saniyelik görsel dolum çizgisi ve geri sayım başlar, süre sonunda işlem kendiliğinden açılır.
- **Sıfır Dış Bağımlılık (Masaüstü):** Masaüstü uygulaması Python'ın yerel `ctypes` ve `tkinter` kütüphanelerini kullanır, harici Python paketi gerektirmez.
- **Bağımsız Yerel Önizleme:** Tarayıcıda çevrimdışı çalışan `preview/preview.html` dosyası ile sistemi doğrudan test edebilirsiniz.
- **Bütünleşik Doğrulama:** `python verify.py` komutu satır sınırlarını (<1000 satır), birim testleri ve Playwright uçtan uca görsel testlerini doğrular.
- **Türkçe Git & Otomatik Release:** Değişiklikleri tek komutla Türkçe açıklama ile GitHub'a pushlar ve otomatik Release paketleri oluşturur.

---

## Hızlı Başlangıç

### 1. Masaüstü Uygulamasını Çalıştırma
```bash
python main.py
```
- Klavyenizin **Numpad Enter** tuşuna arka arkaya iki kez hızlıca basın.
- Fare imlecinizin olduğu ekranda komut çubuğu açılacaktır.
- Bir sayı yazın (örn: `1` Hesap Makinesi, `2` Not Defteri, `4` Google).
- İster `Enter` tuşuna basın, isterseniz 5 saniye dolum çizgisini bekleyin.
- `Escape` tuşu ile çubuğu kapatabilirsiniz.

### 2. Değişiklikleri GitHub'a Türkçe Açıklama ile Pushlama
```bash
# Komut satırından Türkçe açıklama ile:
python scripts/git_push.py "feat: yeni ozellik eklendi"

# Veya yeni surum etiketiyle otomatik release tetikleyerek:
python scripts/git_push.py "chore: surum v1.0.1 yayinlandi" --tag v1.0.1
```

### 3. Yerel Önizleme (Tarayıcı)
`preview/preview.html` dosyasını herhangi bir tarayıcıda açarak tüm klavye ve fare etkileşimlerini simüle edebilirsiniz.

### 4. Bütünleşik Test ve Doğrulama
```bash
python verify.py
```

---

## Proje Yapısı

```
num-launcher/
├── .github/workflows/          # Otomatik GitHub Release iş akışı
├── config.json                 # Yapılandırma ve aksiyon tanımları
├── main.py                     # Masaüstü uygulaması giriş noktası
├── verify.py                   # Bütünleşik test ve satır kontrol scripti
├── scripts/
│   └── git_push.py             # Türkçe commit & push ve release betiği
├── src/
│   ├── config/config_manager.py # SSOT yapılandırma yöneticisi
│   ├── core/
│   │   ├── action_registry.py  # Aksiyon filtreleme ve yürütme
│   │   ├── display_detector.py # Win32 fare ve monitör tespiti
│   │   ├── double_tap_detector.py # Çift basım zamanlayıcı mantığı
│   │   └── numpad_listener.py  # Düşük seviyeli klavye dinleyicisi
│   ├── ui/overlay_bar.py       # Tkinter komut çubuğu arayüzü
│   └── utils/
│       ├── line_counter.py     # 1000 satır sınırı denetleyicisi
│       └── logger.py           # DEBUG günlükleme servisi
├── preview/                    # Bağımsız web önizleme ve simülasyon
│   ├── preview.html
│   ├── preview.css
│   └── preview.js
├── tests/                      # Birim testleri
└── e2e/                        # Playwright görsel & E2E testleri
```

