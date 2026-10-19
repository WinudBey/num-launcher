const { test, expect } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

const PREVIEW_URL = `file://${path.resolve(__dirname, "..", "preview", "preview.html").replace(/\\/g, "/")}`;
const SCREENSHOTS_DIR = path.resolve(__dirname, "..", "screenshots");

test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }
});

test.describe("Num Launcher E2E ve Görsel Doğrulama Testleri", () => {

  test("Sayfa hatasız yüklenmeli ve başlangıç durumu doğru olmalı", async ({ page }) => {
    const consoleErrors = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(PREVIEW_URL);

    // Başlık ve talimat kartını kontrol et
    await expect(page.getByRole("heading", { name: "Num Launcher Yerel Önizleme (Sandbox)" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Kullanım Talimatları" })).toBeVisible();

    // Komut çubuğu başlangıçta gizli olmalı
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeHidden();

    expect(consoleErrors).toHaveLength(0);
  });

  test("Simülasyon butonu ile komut çubuğu açılmalı ve görsel ekran görüntüsü alınmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Butona tıkla
    const triggerBtn = page.getByRole("button", { name: "Enter tuşuna çift basımı simüle et" });
    await triggerBtn.click();

    // Overlay görünür olmalı
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();

    // Giriş kutusu odaklanmış olmalı
    const input = page.getByRole("combobox", { name: "Komut arama ve sayı giriş alanı" });
    await expect(input).toBeVisible();
    await expect(input).toBeFocused();

    // Görsel ekran görüntüsü kaydet
    const screenshotPath = path.join(SCREENSHOTS_DIR, "01_overlay_active.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    expect(fs.existsSync(screenshotPath)).toBeTruthy();
  });

  test("Sayı girişi ile filtreleme, klavye ile seçim ve Enter ile tetikleme doğrulanmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Çubuğu aç
    await page.getByRole("button", { name: "Enter tuşuna çift basımı simüle et" }).click();
    const input = page.getByRole("combobox", { name: "Komut arama ve sayı giriş alanı" });

    // "1" yaz (Hesap Makinesi)
    await input.fill("1");

    // Eylemler listesinde "Hesap Makinesi" seçili olmalı
    const option = page.getByRole("option", { name: "1 Hesap Makinesi" });
    await expect(option).toBeVisible();

    // Filtrelenmiş ekran görüntüsünü kaydet
    const filteredScreenshot = path.join(SCREENSHOTS_DIR, "02_filtered_action.png");
    await page.screenshot({ path: filteredScreenshot, fullPage: true });

    // Enter tuşuna bas
    await input.press("Enter");

    // Çubuk kapanmalı
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeHidden();

    // Sistem günlüğünde aksiyon tetiklendiği görünmeli
    const logOutput = page.getByRole("log");
    await expect(logOutput).toContainText("[AKSİYON TETİKLENDİ] Kod: \"1\" | Başlık: \"Hesap Makinesi\"");

    // Başarılı aksiyon sonrası ekran görüntüsü al
    const executedScreenshot = path.join(SCREENSHOTS_DIR, "03_action_executed.png");
    await page.screenshot({ path: executedScreenshot, fullPage: true });
  });

  test("Escape tuşu ile komut çubuğu kapanmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Çubuğu aç
    await page.getByRole("button", { name: "Enter tuşuna çift basımı simüle et" }).click();
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();

    // Escape bas
    await page.keyboard.press("Escape");
    await expect(overlay).toBeHidden();
  });

  test("Çift Enter klavye basımı ile çubuk açılmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // 100 ms arayla iki kez Enter bas
    await page.keyboard.press("Enter");
    await page.waitForTimeout(100);
    await page.keyboard.press("Enter");

    // Çubuk otomatik açılmalı
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();
  });

  test("Sayı yazıldığında Enter basılmadan 5 saniye sonra otomatik uygulanmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Çubuğu aç
    await page.getByRole("button", { name: "Enter tuşuna çift basımı simüle et" }).click();
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();

    const input = page.getByRole("combobox", { name: "Komut arama ve sayı giriş alanı" });
    // "2" yaz (Not Defteri)
    await input.fill("2");

    // Geri sayım rozeti görünür olmalı
    const countdownBadge = page.locator("#countdown-badge");
    await expect(countdownBadge).toBeVisible();
    await expect(countdownBadge).toContainText("⏱");

    // Geri sayım anında ekran görüntüsü al
    const countdownScreenshot = path.join(SCREENSHOTS_DIR, "04_countdown_active.png");
    await page.screenshot({ path: countdownScreenshot, fullPage: true });
    expect(fs.existsSync(countdownScreenshot)).toBeTruthy();

    // Enter'a basmadan 5.2 saniye bekle
    await page.waitForTimeout(5200);

    // Çubuk kendiliğinden kapanmış olmalı
    await expect(overlay).toBeHidden();

    // Günlükte Not Defteri eyleminin otomatik tetiklendiği doğrulanmalı
    const logOutput = page.getByRole("log");
    await expect(logOutput).toContainText("[AKSİYON TETİKLENDİ] Kod: \"2\" | Başlık: \"Not Defteri\"");

    // Otomatik çalıştırma sonrası ekran görüntüsü al
    const autoExecScreenshot = path.join(SCREENSHOTS_DIR, "05_auto_executed_after_5s.png");
    await page.screenshot({ path: autoExecScreenshot, fullPage: true });
    expect(fs.existsSync(autoExecScreenshot)).toBeTruthy();
  });

  test("Sayı yazıldığında animasyonlu dolum çizgisi görünmeli ve dolmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Çubuğu aç
    await page.getByRole("button", { name: "Enter tuşuna çift basımı simüle et" }).click();
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();

    const input = page.getByRole("combobox", { name: "Komut arama ve sayı giriş alanı" });
    // "1" yaz (Hesap Makinesi)
    await input.fill("1");

    // İlerleme çubuğu öğesini bul
    const progressFill = page.locator("#progress-bar-fill");
    await expect(progressFill).toBeVisible();

    // 2 saniye bekle ve dolum çizgisinin genişliğini kontrol et
    await page.waitForTimeout(2000);

    const widthStyle = await progressFill.evaluate((el) => el.style.width);
    const widthNum = parseFloat(widthStyle);
    expect(widthNum).toBeGreaterThan(20);

    // Dolum çizgisi ekran görüntüsü al
    const fillingScreenshot = path.join(SCREENSHOTS_DIR, "06_progress_bar_filling.png");
    await page.screenshot({ path: fillingScreenshot, fullPage: true });
    expect(fs.existsSync(fillingScreenshot)).toBeTruthy();

    // Dolumun tamamlanmasını bekle (kalan 3.3 sn)
    await page.waitForTimeout(3300);

    // Çubuk kapanmalı
    await expect(overlay).toBeHidden();

    // Eylemin tamamlandığı logdan doğrulanmalı
    const logOutput = page.getByRole("log");
    await expect(logOutput).toContainText("[AKSİYON TETİKLENDİ] Kod: \"1\" | Başlık: \"Hesap Makinesi\"");
  });

  test("Ayarlar menüsü açılmalı, kısayol tablosu listelenmeli ve ekran görüntüsü alınmalı", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Ayarlar butonuna tıkla
    const settingsBtn = page.getByRole("button", { name: "Ayarlar menüsünü aç" });
    await expect(settingsBtn).toBeVisible();
    await settingsBtn.click();

    // Ayarlar modalı görünür olmalı
    const modal = page.locator("#settings-modal");
    await expect(modal).toBeVisible();

    // Kısayol tablosunda en az 6 satır olmalı
    const rows = page.locator("#shortcuts-tbody tr");
    await expect(rows).toHaveCount(6);

    // Ayarlar menüsü ekran görüntüsü al
    const settingsScreenshot = path.join(SCREENSHOTS_DIR, "07_settings_modal.png");
    await page.screenshot({ path: settingsScreenshot, fullPage: true });
    expect(fs.existsSync(settingsScreenshot)).toBeTruthy();

    // Kapat butonuna bas
    await page.locator("#btn-close-settings").click();
    await expect(modal).toBeHidden();
  });

  test("Yeni kısayol elle eklenmeli, kaydedilmeli ve komut çubuğunda kullanılabilmeli", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Ayarları aç
    await page.locator("#btn-open-settings").click();
    const modal = page.locator("#settings-modal");
    await expect(modal).toBeVisible();

    // Formu doldur
    await page.locator("#input-code").fill("8");
    await page.locator("#input-title").fill("Spotify Müzik");
    await page.locator("#input-desc").fill("Spotify uygulamasını açar.");
    await page.locator("#select-type").selectOption("cmd");
    await page.locator("#input-cmd").fill("spotify.exe");

    // "Listeye Ekle" butonuna bas
    await page.locator("#btn-save-shortcut").click();

    // Tabloda yeni öğe (7. satır) görünmeli
    const rows = page.locator("#shortcuts-tbody tr");
    await expect(rows).toHaveCount(7);
    await expect(page.locator("#shortcuts-tbody")).toContainText("Spotify Müzik");

    // Ayarları kaydet
    await page.locator("#btn-save-settings").click();
    await expect(modal).toBeHidden();

    // Komut çubuğunu aç
    await page.locator("#btn-trigger-double-enter").click();
    const overlay = page.getByRole("dialog", { name: "Numpad Komut Çubuğu" });
    await expect(overlay).toBeVisible();

    // "8" yaz
    const input = page.getByRole("combobox", { name: "Komut arama ve sayı giriş alanı" });
    await input.fill("8");

    // Yeni kısayol önerisi görünmeli
    const spotifyOption = page.locator("#action-list .action-item", { hasText: "Spotify Müzik" });
    await expect(spotifyOption).toBeVisible();

    // Ekran görüntüsü al
    const newActionScreenshot = path.join(SCREENSHOTS_DIR, "08_new_shortcut_used.png");
    await page.screenshot({ path: newActionScreenshot, fullPage: true });
    expect(fs.existsSync(newActionScreenshot)).toBeTruthy();

    // Enter'a basarak çalıştır
    await input.press("Enter");
    await expect(overlay).toBeHidden();

    // Sistem günlüğünde çalıştığı doğrulanmalı
    const logOutput = page.getByRole("log");
    await expect(logOutput).toContainText("[AKSİYON TETİKLENDİ] Kod: \"8\" | Başlık: \"Spotify Müzik\"");
  });

  test("Kısayol sırası ok butonlarıyla değiştirilebilmeli", async ({ page }) => {
    await page.goto(PREVIEW_URL);

    // Ayarları aç
    await page.locator("#btn-open-settings").click();
    await expect(page.locator("#settings-modal")).toBeVisible();

    // 2. sıradaki elemanın (Not Defteri) yukarı ok butonuna tıkla
    const secondRowUpBtn = page.locator("#shortcuts-tbody tr:nth-child(2) .btn-up");
    await secondRowUpBtn.click();

    // Şimdi 1. satır "Not Defteri" olmalı
    const firstRowText = await page.locator("#shortcuts-tbody tr:nth-child(1)").textContent();
    expect(firstRowText).toContain("Not Defteri");

    // Sıralama değişikliği ekran görüntüsü al
    const reorderedScreenshot = path.join(SCREENSHOTS_DIR, "09_shortcut_reordered.png");
    await page.screenshot({ path: reorderedScreenshot, fullPage: true });
    expect(fs.existsSync(reorderedScreenshot)).toBeTruthy();

    // Ayarları kaydet
    await page.locator("#btn-save-settings").click();
    await expect(page.locator("#settings-modal")).toBeHidden();

    // Komut çubuğunu aç
    await page.locator("#btn-trigger-double-enter").click();
    // Komut çubuğundaki ilk öneri Not Defteri olmalı
    const firstActionItem = page.locator("#action-list .action-item:first-child");
    await expect(firstActionItem).toContainText("Not Defteri");
  });

});


