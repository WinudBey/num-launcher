/**
 * Numpad Bar Yerel Önizleme ve Etkileşim Scripti
 * W3C WAI-ARIA, klavye navigasyonu ve dokunmatik hareketleri destekler.
 */

// Varsayılan Eylem Listesi (SSOT ile uyumlu)
const MOCK_ACTIONS = [
  { code: "1", title: "Hesap Makinesi", description: "Windows Hesap Makinesi uygulamasını açar.", type: "cmd", command: "calc.exe" },
  { code: "2", title: "Not Defteri", description: "Hızlı not almak için Notepad açar.", type: "cmd", command: "notepad.exe" },
  { code: "3", title: "Görev Yöneticisi", description: "Windows Görev Yöneticisini başlatır.", type: "cmd", command: "taskmgr.exe" },
  { code: "4", title: "Tarayıcı - Google", description: "Varsayılan tarayıcıda Google ana sayfasını açar.", type: "url", command: "https://www.google.com" },
  { code: "5", title: "Terminal (PowerShell)", description: "Windows PowerShell penceresi açar.", type: "cmd", command: "powershell.exe" },
  { code: "0", title: "Ekranı Kilitle", description: "Oturumu güvenli bir şekilde kilitler.", type: "cmd", command: "rundll32.exe user32.dll,LockWorkStation" }
];

class PreviewApp {
  constructor() {
    const savedActions = localStorage.getItem("num_launcher_actions");
    if (savedActions) {
      try {
        this.actions = JSON.parse(savedActions);
      } catch (e) {
        this.actions = [...MOCK_ACTIONS];
      }
    } else {
      this.actions = [...MOCK_ACTIONS];
    }

    this.filteredActions = [...this.actions];
    this.selectedIndex = 0;
    this.isOpen = false;
    this.isSettingsOpen = false;
    this.editingIndex = null;
    this.lastEnterPressTime = 0;
    this.doubleTapThresholdMs = 400;

    // Otomatik Çalıştırma (5 saniye)
    this.autoExecuteDelaySec = 5;
    this.autoExecTimer = null;
    this.countdownInterval = null;
    this.countdownRemaining = 0;

    // Dokunmatik kaydırma takibi (Touch Swipe)
    this.touchStartY = 0;

    this.initElements();
    this.bindEvents();
    this.renderActions();
  }

  initElements() {
    this.overlayContainer = document.getElementById("overlay-container");
    this.overlayBackdrop = document.getElementById("overlay-backdrop");
    this.commandBar = document.getElementById("command-bar");
    this.commandInput = document.getElementById("command-input");
    this.countdownBadge = document.getElementById("countdown-badge");
    this.progressBarFill = document.getElementById("progress-bar-fill");
    this.actionList = document.getElementById("action-list");
    this.logOutput = document.getElementById("log-output");
    this.btnTrigger = document.getElementById("btn-trigger-double-enter");
    this.btnResetLog = document.getElementById("btn-reset-log");

    // Ayarlar Modalı Elementleri
    this.settingsModal = document.getElementById("settings-modal");
    this.settingsBackdrop = document.getElementById("settings-backdrop");
    this.btnOpenSettings = document.getElementById("btn-open-settings");
    this.btnBarSettings = document.getElementById("btn-bar-settings");
    this.btnCloseSettings = document.getElementById("btn-close-settings");
    this.btnCloseSettingsX = document.getElementById("btn-close-settings-x");
    this.btnSaveSettings = document.getElementById("btn-save-settings");
    this.shortcutsTbody = document.getElementById("shortcuts-tbody");

    // Form Elementleri
    this.inputCode = document.getElementById("input-code");
    this.inputTitle = document.getElementById("input-title");
    this.selectType = document.getElementById("select-type");
    this.inputDesc = document.getElementById("input-desc");
    this.inputCmd = document.getElementById("input-cmd");
    this.btnSaveShortcut = document.getElementById("btn-save-shortcut");
    this.btnCancelEdit = document.getElementById("btn-cancel-edit");
    this.formHeading = document.getElementById("form-heading");
  }

  bindEvents() {
    // Çift Enter Algılama (Numpad veya Standart Enter)
    window.addEventListener("keydown", (e) => this.handleGlobalKeyDown(e));

    // Buton tetikleyicileri
    if (this.btnTrigger) {
      this.btnTrigger.addEventListener("click", () => this.openOverlay());
    }

    if (this.btnResetLog) {
      this.btnResetLog.addEventListener("click", () => this.clearLog());
    }

    // Ayarlar Açma Butonları
    if (this.btnOpenSettings) {
      this.btnOpenSettings.addEventListener("click", () => this.openSettings());
    }
    if (this.btnBarSettings) {
      this.btnBarSettings.addEventListener("click", () => this.openSettings());
    }

    // Ayarlar Kapatma Butonları
    if (this.btnCloseSettings) {
      this.btnCloseSettings.addEventListener("click", () => this.closeSettings());
    }
    if (this.btnCloseSettingsX) {
      this.btnCloseSettingsX.addEventListener("click", () => this.closeSettings());
    }
    if (this.settingsBackdrop) {
      this.settingsBackdrop.addEventListener("click", () => this.closeSettings());
    }

    // Ayarlar Kaydetme ve Form Butonları
    if (this.btnSaveSettings) {
      this.btnSaveSettings.addEventListener("click", () => this.saveSettings());
    }
    if (this.btnSaveShortcut) {
      this.btnSaveShortcut.addEventListener("click", () => this.handleSaveShortcut());
    }
    if (this.btnCancelEdit) {
      this.btnCancelEdit.addEventListener("click", () => this.resetForm());
    }

    // Modal içi klavye olayları
    if (this.commandInput) {
      this.commandInput.addEventListener("input", () => this.handleInput());
      this.commandInput.addEventListener("keydown", (e) => this.handleInputKeyDown(e));
    }

    // Dışarı tıklama ile kapatma
    if (this.overlayBackdrop) {
      this.overlayBackdrop.addEventListener("click", () => this.closeOverlay());
    }

    // Mobil Dokunmatik Kaydırma (Touch Swipe-Up ile Kapatma)
    if (this.commandBar) {
      this.commandBar.addEventListener("touchstart", (e) => {
        this.touchStartY = e.touches[0].clientY;
      }, { passive: true });

      this.commandBar.addEventListener("touchend", (e) => {
        const touchEndY = e.changedTouches[0].clientY;
        const diffY = this.touchStartY - touchEndY;
        // Yukarı 50px kaydırma yapıldıysa kapat
        if (diffY > 50) {
          this.log("Yukarı kaydırma (swipe-up) hareketi algılandı. Çubuk kapatılıyor.", "info");
          this.closeOverlay();
        }
      }, { passive: true });
    }
  }

  handleGlobalKeyDown(e) {
    if (e.key === "Enter") {
      const now = performance.now();
      const elapsed = now - this.lastEnterPressTime;

      if (!this.isOpen && this.lastEnterPressTime > 0 && elapsed > 0 && elapsed <= this.doubleTapThresholdMs) {
        e.preventDefault();
        this.lastEnterPressTime = 0;
        this.log(`Çift Enter basımı algılandı (${elapsed.toFixed(0)} ms). Çubuk açılıyor.`, "system");
        this.openOverlay();
        return;
      }
      this.lastEnterPressTime = now;
    }

    if (e.key === "Escape") {
      if (this.isSettingsOpen) {
        e.preventDefault();
        this.closeSettings();
        return;
      }
      if (this.isOpen) {
        e.preventDefault();
        this.closeOverlay();
      }
    }
  }

  handleInput() {
    const query = this.commandInput.value.trim().toLowerCase();
    if (!query) {
      this.filteredActions = [...this.actions];
    } else {
      const exactCode = [];
      const prefixCode = [];
      const textMatches = [];

      this.actions.forEach(action => {
        const code = action.code.toLowerCase();
        const title = action.title.toLowerCase();
        const desc = action.description.toLowerCase();

        if (code === query) {
          exactCode.push(action);
        } else if (code.startsWith(query)) {
          prefixCode.push(action);
        } else if (title.includes(query) || desc.includes(query)) {
          textMatches.push(action);
        }
      });

      this.filteredActions = [...exactCode, ...prefixCode, ...textMatches];
    }

    this.selectedIndex = 0;
    this.renderActions();
    this.startAutoExecuteTimer();
  }

  cancelAutoExecuteTimer() {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.autoExecTimer) {
      clearTimeout(this.autoExecTimer);
      this.autoExecTimer = null;
    }
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    this.countdownRemaining = 0;
    if (this.progressBarFill) {
      this.progressBarFill.style.width = "0%";
    }
    if (this.countdownBadge) {
      this.countdownBadge.classList.add("hidden");
      this.countdownBadge.textContent = "";
    }
  }

  startAutoExecuteTimer() {
    this.cancelAutoExecuteTimer();
    if (this.autoExecuteDelaySec <= 0) return;

    const query = this.commandInput.value.trim();
    if (!query || this.filteredActions.length === 0) return;

    this.progressStartTime = performance.now();
    const durationMs = this.autoExecuteDelaySec * 1000;

    if (this.countdownBadge) {
      this.countdownBadge.textContent = `⏱ ${this.autoExecuteDelaySec}s`;
      this.countdownBadge.classList.remove("hidden");
    }

    const step = (now) => {
      if (!this.isOpen) {
        this.cancelAutoExecuteTimer();
        return;
      }

      const elapsed = now - this.progressStartTime;
      const progress = Math.min(1, elapsed / durationMs);

      if (this.progressBarFill) {
        this.progressBarFill.style.width = `${(progress * 100).toFixed(1)}%`;
      }

      const remainingSec = Math.max(0, Math.ceil((durationMs - elapsed) / 1000));
      if (this.countdownBadge) {
        this.countdownBadge.textContent = `⏱ ${remainingSec}s`;
      }

      if (progress < 1) {
        this.animFrameId = requestAnimationFrame(step);
      } else {
        this.cancelAutoExecuteTimer();
        if (this.isOpen && this.filteredActions.length > 0 && this.selectedIndex < this.filteredActions.length) {
          const action = this.filteredActions[this.selectedIndex];
          this.log(`5 saniyelik çizgi dolumu tamamlandı: [${action.code}] ${action.title} otomatik çalıştırılıyor.`, "action");
          this.executeAction(action);
        }
      }
    };

    this.animFrameId = requestAnimationFrame(step);
  }

  handleInputKeyDown(e) {
    e.stopPropagation();
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (this.filteredActions.length > 0) {
        this.selectedIndex = (this.selectedIndex + 1) % this.filteredActions.length;
        this.renderActions();
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (this.filteredActions.length > 0) {
        this.selectedIndex = (this.selectedIndex - 1 + this.filteredActions.length) % this.filteredActions.length;
        this.renderActions();
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      this.cancelAutoExecuteTimer();
      this.lastEnterPressTime = 0;
      if (this.filteredActions.length > 0 && this.selectedIndex < this.filteredActions.length) {
        const selected = this.filteredActions[this.selectedIndex];
        this.executeAction(selected);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      this.cancelAutoExecuteTimer();
      this.closeOverlay();
    }
  }

  openOverlay() {
    this.cancelAutoExecuteTimer();
    this.isOpen = true;
    this.lastEnterPressTime = 0;
    this.overlayContainer.classList.remove("hidden");
    this.commandInput.value = "";
    this.filteredActions = [...this.actions];
    this.selectedIndex = 0;
    this.renderActions();

    setTimeout(() => {
      this.commandInput.focus();
    }, 50);

    this.log("Komut çubuğu açıldı ve fare konumundaki monitöre ortalandı.", "system");
  }

  closeOverlay() {
    if (!this.isOpen) return;
    this.cancelAutoExecuteTimer();
    this.isOpen = false;
    this.overlayContainer.classList.add("hidden");
    this.log("Komut çubuğu kapatıldı.", "info");
  }

  executeAction(action) {
    this.cancelAutoExecuteTimer();
    this.closeOverlay();
    this.log(
      `[AKSİYON TETİKLENDİ] Kod: "${action.code}" | Başlık: "${action.title}" | Komut: "${action.command}" (${action.type})`,
      "action"
    );
  }

  renderActions() {
    this.actionList.innerHTML = "";

    if (this.filteredActions.length === 0) {
      const emptyLi = document.createElement("li");
      emptyLi.className = "action-empty";
      emptyLi.textContent = "Eşleşen komut bulunamadı.";
      this.actionList.appendChild(emptyLi);
      return;
    }

    this.filteredActions.slice(0, 6).forEach((action, index) => {
      const isSelected = index === this.selectedIndex;
      const li = document.createElement("li");
      li.className = `action-item ${isSelected ? "selected" : ""}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", isSelected ? "true" : "false");
      li.id = `action-opt-${index}`;

      li.innerHTML = `
        <span class="action-code-badge">${action.code}</span>
        <div class="action-details">
          <span class="action-title">${action.title}</span>
          <span class="action-desc">${action.description}</span>
        </div>
      `;

      li.addEventListener("click", () => this.executeAction(action));
      this.actionList.appendChild(li);

      if (isSelected && this.commandInput) {
        this.commandInput.setAttribute("aria-activedescendant", li.id);
      }
    });
  }

  log(message, type = "info") {
    if (!this.logOutput) return;
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    this.logOutput.appendChild(entry);
    this.logOutput.scrollTop = this.logOutput.scrollHeight;
  }

  openSettings() {
    this.cancelAutoExecuteTimer();
    this.closeOverlay();
    this.isSettingsOpen = true;
    if (this.settingsModal) {
      this.settingsModal.classList.remove("hidden");
    }
    this.renderShortcutsTable();
    this.log("Ayarlar menüsü açıldı.", "system");
  }

  closeSettings() {
    this.isSettingsOpen = false;
    if (this.settingsModal) {
      this.settingsModal.classList.add("hidden");
    }
    this.resetForm();
    this.log("Ayarlar menüsü kapatıldı.", "info");
  }

  renderShortcutsTable() {
    if (!this.shortcutsTbody) return;
    this.shortcutsTbody.innerHTML = "";

    this.actions.forEach((act, index) => {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td style="text-align: center; color: var(--text-muted);">${index + 1}</td>
        <td style="text-align: center;"><span class="action-code-badge">${act.code}</span></td>
        <td><strong>${act.title}</strong><br><small style="color: var(--text-muted);">${act.description || ""}</small></td>
        <td style="text-align: center;"><code>${act.type || "cmd"}</code></td>
        <td style="font-family: monospace; font-size: 0.82rem; color: var(--text-muted);">${act.command}</td>
        <td>
          <div class="table-btn-group">
            <button class="btn-tbl btn-up" data-idx="${index}" title="Yukarı Taşı" aria-label="Kısayolu yukarı taşı">⬆️</button>
            <button class="btn-tbl btn-down" data-idx="${index}" title="Aşağı Taşı" aria-label="Kısayolu aşağı taşı">⬇️</button>
            <button class="btn-tbl btn-edit" data-idx="${index}" title="Düzenle" aria-label="Kısayolu düzenle">✏️</button>
            <button class="btn-tbl danger btn-del" data-idx="${index}" title="Sil" aria-label="Kısayolu sil">🗑️</button>
          </div>
        </td>
      `;

      // Buton olayları
      tr.querySelector(".btn-up").addEventListener("click", () => this.moveUp(index));
      tr.querySelector(".btn-down").addEventListener("click", () => this.moveDown(index));
      tr.querySelector(".btn-edit").addEventListener("click", () => this.startEditShortcut(index));
      tr.querySelector(".btn-del").addEventListener("click", () => this.deleteShortcut(index));

      this.shortcutsTbody.appendChild(tr);
    });
  }

  moveUp(index) {
    if (index <= 0) return;
    const item = this.actions.splice(index, 1)[0];
    this.actions.splice(index - 1, 0, item);
    this.filteredActions = [...this.actions];
    this.renderShortcutsTable();
    this.renderActions();
    this.log(`Kısayol sırası değiştirildi (yukarı): "${item.title}"`, "info");
  }

  moveDown(index) {
    if (index >= this.actions.length - 1) return;
    const item = this.actions.splice(index, 1)[0];
    this.actions.splice(index + 1, 0, item);
    this.filteredActions = [...this.actions];
    this.renderShortcutsTable();
    this.renderActions();
    this.log(`Kısayol sırası değiştirildi (aşağı): "${item.title}"`, "info");
  }

  startEditShortcut(index) {
    if (index < 0 || index >= this.actions.length) return;
    const act = this.actions[index];
    this.editingIndex = index;

    if (this.inputCode) this.inputCode.value = act.code;
    if (this.inputTitle) this.inputTitle.value = act.title;
    if (this.selectType) this.selectType.value = act.type || "cmd";
    if (this.inputDesc) this.inputDesc.value = act.description || "";
    if (this.inputCmd) this.inputCmd.value = act.command;

    if (this.btnSaveShortcut) this.btnSaveShortcut.textContent = "✏️ Güncelle";
    if (this.btnCancelEdit) this.btnCancelEdit.classList.remove("hidden");
    if (this.formHeading) this.formHeading.textContent = `Kısayolu Düzenle: ${act.title}`;
    if (this.inputCode) this.inputCode.focus();
  }

  resetForm() {
    this.editingIndex = null;
    if (this.inputCode) this.inputCode.value = "";
    if (this.inputTitle) this.inputTitle.value = "";
    if (this.selectType) this.selectType.value = "cmd";
    if (this.inputDesc) this.inputDesc.value = "";
    if (this.inputCmd) this.inputCmd.value = "";

    if (this.btnSaveShortcut) this.btnSaveShortcut.textContent = "➕ Listeye Ekle";
    if (this.btnCancelEdit) this.btnCancelEdit.classList.add("hidden");
    if (this.formHeading) this.formHeading.textContent = "Yeni Kısayol Ekle";
  }

  handleSaveShortcut() {
    const code = this.inputCode ? this.inputCode.value.trim() : "";
    const title = this.inputTitle ? this.inputTitle.value.trim() : "";
    const type = this.selectType ? this.selectType.value : "cmd";
    const desc = this.inputDesc ? this.inputDesc.value.trim() : "";
    const cmd = this.inputCmd ? this.inputCmd.value.trim() : "";

    if (!code || !title || !cmd) {
      this.log("Kısayol eklenemedi: Kod, Başlık ve Komut zorunludur.", "info");
      alert("Kod, Başlık ve Komut alanları boş bırakılamaz.");
      return;
    }

    const actionData = { code, title, description: desc, type, command: cmd };

    if (this.editingIndex !== null && this.editingIndex >= 0 && this.editingIndex < this.actions.length) {
      this.actions[this.editingIndex] = actionData;
      this.log(`Kısayol güncellendi: [${code}] ${title}`, "info");
    } else {
      this.actions.push(actionData);
      this.log(`Yeni kısayol eklendi: [${code}] ${title}`, "info");
    }

    this.filteredActions = [...this.actions];
    this.renderShortcutsTable();
    this.renderActions();
    this.resetForm();
  }

  deleteShortcut(index) {
    if (index < 0 || index >= this.actions.length) return;
    const removed = this.actions.splice(index, 1)[0];
    this.filteredActions = [...this.actions];
    this.renderShortcutsTable();
    this.renderActions();
    this.resetForm();
    this.log(`Kısayol silindi: [${removed.code}] ${removed.title}`, "info");
  }

  saveSettings() {
    try {
      localStorage.setItem("num_launcher_actions", JSON.stringify(this.actions));
    } catch (e) {
      console.error("localStorage kaydetme hatası:", e);
    }
    this.filteredActions = [...this.actions];
    this.renderActions();
    this.log(`[AYARLAR] Kısayollar başarıyla kaydedildi. Toplam: ${this.actions.length}`, "system");
    this.closeSettings();
  }

  clearLog() {
    if (!this.logOutput) return;
    this.logOutput.innerHTML = "";
    this.log("Günlük temizlendi.", "info");
  }
}

// Sayfa yüklendiğinde başlat
window.addEventListener("DOMContentLoaded", () => {
  window.__previewApp = new PreviewApp();
});
