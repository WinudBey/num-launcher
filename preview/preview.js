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
    this.actions = [...MOCK_ACTIONS];
    this.filteredActions = [...this.actions];
    this.selectedIndex = 0;
    this.isOpen = false;
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

    if (e.key === "Escape" && this.isOpen) {
      e.preventDefault();
      this.closeOverlay();
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
