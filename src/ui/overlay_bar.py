"""Komut çubuğu grafik arayüz modülü.

Tkinter kullanarak kenarlıksız, modern, odaklanabilir ve fare monitörüne
otomatik yerleşen bir komut çubuğu penceresi sunar.
"""

import ctypes
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Any, Callable, Dict, List, Optional
from src.config.config_manager import ConfigManager
from src.core.action_registry import ActionExecutionResult, ActionRegistry
from src.core.display_detector import calculate_centered_window_position
from src.utils.logger import get_logger

logger = get_logger()


class OverlayBar:
    """Masaüstü komut çubuğu pencere sınıfı."""

    def __init__(
        self,
        registry: ActionRegistry,
        config: Dict[str, Any],
        on_action_executed: Optional[Callable[[ActionExecutionResult], None]] = None,
        config_manager: Optional[ConfigManager] = None
    ) -> None:
        """OverlayBar sınıfını başlatır.

        Args:
            registry: Aksiyon eşleştirme ve yürütme nesnesi.
            config: Görsel ve davranış yapılandırması.
            on_action_executed: Aksiyon çalıştırıldığında çağrılacak geribildirim fonksiyonu.
            config_manager: Yapılandırma yöneticisi nesnesi.
        """
        self.registry = registry
        self.config = config
        self.config_manager = config_manager or ConfigManager()
        self.on_action_executed = on_action_executed
        self.settings_window: Optional[Any] = None

        ui_conf = config.get("ui", {})
        self.base_width = int(ui_conf.get("width", 640))
        self.compact_height = int(ui_conf.get("height", 72))
        self.expanded_height = int(ui_conf.get("expanded_height", 380))
        self.auto_execute_delay_sec = float(ui_conf.get("auto_execute_delay_sec", 5.0))
        self.theme = ui_conf.get("theme", {})

        self.root: Optional[tk.Tk] = None
        self._is_visible = False
        self._selected_index = 0
        self._filtered_actions: List[Dict[str, Any]] = []
        self._auto_exec_timer_id: Optional[str] = None
        self._countdown_remaining: int = 0
        self._progress_start_time: float = 0.0

        self._build_ui()

    def _build_ui(self) -> None:
        """Pencere bileşenlerini ve düzenini oluşturur."""
        self.root = tk.Tk()
        self.root.title("Num Launcher")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.theme.get("bg_color", "#181825"))

        # Ana çerçeve (kenarlık efekti ile)
        self.container = tk.Frame(
            self.root,
            bg=self.theme.get("bg_color", "#181825"),
            highlightbackground=self.theme.get("border_color", "#313244"),
            highlightthickness=2,
            padx=16,
            pady=12
        )
        self.container.pack(fill=tk.BOTH, expand=True)

        # Giriş kutusu çerçevesi
        input_frame = tk.Frame(self.container, bg=self.theme.get("input_bg", "#1e1e2e"), padx=10, pady=8)
        input_frame.pack(fill=tk.X, pady=(0, 8))

        # Numpad Rozeti / İkonu
        badge_lbl = tk.Label(
            input_frame,
            text="NUM",
            bg=self.theme.get("accent_color", "#89b4fa"),
            fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=2
        )
        badge_lbl.pack(side=tk.LEFT, padx=(0, 10))

        # Giriş Kutusu (Entry)
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self._on_text_changed)

        entry_font = ("Segoe UI", 16)
        self.entry = tk.Entry(
            input_frame,
            textvariable=self.entry_var,
            bg=self.theme.get("input_bg", "#1e1e2e"),
            fg=self.theme.get("text_color", "#cdd6f4"),
            insertbackground=self.theme.get("accent_color", "#89b4fa"),
            relief=tk.FLAT,
            font=entry_font,
            bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Geri sayım rozeti
        self.timer_lbl = tk.Label(
            input_frame,
            text="",
            bg=self.theme.get("input_bg", "#1e1e2e"),
            fg=self.theme.get("accent_color", "#89b4fa"),
            font=("Segoe UI", 11, "bold"),
            padx=6,
            pady=2
        )
        self.timer_lbl.pack(side=tk.RIGHT, padx=(4, 0))

        # Ayarlar Butonu (⚙️)
        self.btn_settings = tk.Button(
            input_frame,
            text="⚙️",
            bg=self.theme.get("input_bg", "#1e1e2e"),
            fg=self.theme.get("accent_color", "#89b4fa"),
            activebackground=self.theme.get("selected_bg", "#45475a"),
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            font=("Segoe UI", 11),
            cursor="hand2",
            padx=4,
            pady=2,
            command=self.open_settings
        )
        self.btn_settings.pack(side=tk.RIGHT, padx=(4, 0))

        # İlerleme Çubuğu Tuvali (3 px modern dolum çizgisi)
        self.progress_canvas = tk.Canvas(
            self.container,
            height=3,
            bg=self.theme.get("border_color", "#313244"),
            highlightthickness=0,
            bd=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 8))

        # Liste çerçevesi (Öneriler)
        self.list_frame = tk.Frame(self.container, bg=self.theme.get("bg_color", "#181825"))
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # Klavye Olay Bağlantıları
        self.entry.bind("<Return>", self._on_enter_pressed)
        self.entry.bind("<KP_Enter>", self._on_enter_pressed)
        self.entry.bind("<Escape>", lambda e: self.hide())
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Down>", self._on_arrow_down)
        self.root.bind("<FocusOut>", self._on_focus_out)

        # Başlangıçta gizle
        self.root.withdraw()

    def show(self) -> None:
        """Komut çubuğunu fare imlecinin bulunduğu monitörde gösterir."""
        if not self.root:
            return

        self._cancel_auto_execute_timer()
        self._selected_index = 0
        self.entry_var.set("")
        self._refresh_action_list()

        # Fare monitörüne göre konumu hesapla
        pos = calculate_centered_window_position(self.base_width, self.expanded_height)
        geo_str = f"{pos.width}x{pos.height}+{pos.x}+{pos.y}"

        logger.debug("Overlay açılıyor. Geometri: %s", geo_str)
        self.root.geometry(geo_str)
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.entry.focus_set()

        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            logger.debug("SetForegroundWindow hatası: %s", e)

        self._opened_at = time.time()
        self._is_visible = True
        self.root.after(30, lambda: self.entry.focus_set())

    def hide(self) -> None:
        """Komut çubuğunu gizler."""
        self._cancel_auto_execute_timer()
        if self.root and self._is_visible:
            logger.debug("Overlay gizleniyor.")
            self.root.withdraw()
            self._is_visible = False

    def toggle(self) -> None:
        """Komut çubuğunu durumuna göre açar veya kapatır."""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def open_settings(self) -> None:
        """Ayarlar penceresini açar."""
        self._cancel_auto_execute_timer()
        if self.settings_window and self.settings_window.window and self.settings_window.window.winfo_exists():
            self.settings_window.window.lift()
            self.settings_window.window.focus_force()
            return

        from src.ui.settings_window import SettingsWindow
        self.settings_window = SettingsWindow(
            parent=self.root,
            config_manager=self.config_manager,
            on_actions_updated=self._on_actions_updated
        )

    def _on_actions_updated(self, new_actions: List[Dict[str, Any]]) -> None:
        """Ayarlar penceresinden kaydedilen yeni eylemleri komut motoruna uygular."""
        self.registry.set_actions(new_actions)
        self._refresh_action_list()
        logger.info("OverlayBar eylem listesi güncellendi. Toplam eleman: %d", len(new_actions))

    def _on_focus_out(self, event: Any) -> None:
        """Pencere odağını kaybettiğinde gizler."""
        # Açılış anındaki geçici odak kaybını engelle (0.3 sn tolerans)
        if hasattr(self, "_opened_at") and (time.time() - self._opened_at < 0.3):
            return

        # Ayarlar penceresi açıkken çubuğu kapatma
        if self.settings_window and self.settings_window.window and self.settings_window.window.winfo_exists():
            return

        if self.root and self.root.focus_get() is None:
            self.hide()

    def _on_text_changed(self, *args: Any) -> None:
        """Kullanıcı yazı yazdıkça öneri listesini günceller ve zamanlayıcıyı başlatır."""
        self._selected_index = 0
        self._refresh_action_list()
        self._restart_auto_execute_timer()

    def _cancel_auto_execute_timer(self) -> None:
        """Aktif otomatik çalıştırma zamanlayıcısını ve dolum çizgisini iptal eder."""
        if self._auto_exec_timer_id and self.root:
            try:
                self.root.after_cancel(self._auto_exec_timer_id)
            except Exception as e:
                logger.debug("after_cancel hatası: %s", e)
            self._auto_exec_timer_id = None
        self._countdown_remaining = 0
        if hasattr(self, "progress_canvas") and self.progress_canvas:
            self.progress_canvas.delete("all")
        if hasattr(self, "timer_lbl") and self.timer_lbl:
            self.timer_lbl.config(text="")

    def _restart_auto_execute_timer(self) -> None:
        """Kullanıcı yazı girdiğinde geri sayım zamanlayıcısını ve dolum çizgisini başlatır."""
        self._cancel_auto_execute_timer()

        if self.auto_execute_delay_sec <= 0:
            return

        query = self.entry_var.get().strip()
        if not query or not self._filtered_actions:
            return

        self._progress_start_time = time.time()
        self._animate_progress_tick()

    def _animate_progress_tick(self) -> None:
        """Dolum çizgisini ve geri sayımı 50 FPS (20 ms) ile akıcı şekilde günceller."""
        if not self._is_visible or not self.root:
            self._cancel_auto_execute_timer()
            return

        query = self.entry_var.get().strip()
        if not query or not self._filtered_actions:
            self._cancel_auto_execute_timer()
            return

        elapsed = time.time() - self._progress_start_time
        total_duration = max(0.1, self.auto_execute_delay_sec)
        progress = min(1.0, elapsed / total_duration)

        # Tuval genişliğini al
        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.base_width - 32

        fill_width = int(canvas_width * progress)

        # Çizgiyi yeniden çiz
        self.progress_canvas.delete("all")
        if fill_width > 0:
            self.progress_canvas.create_rectangle(
                0, 0, fill_width, 3,
                fill=self.theme.get("accent_color", "#89b4fa"),
                width=0
            )

        # Kalan saniyeyi rozette göster
        remaining_sec = max(0, int(total_duration - elapsed + 0.99))
        self.timer_lbl.config(text=f"⏱ {remaining_sec}s")

        # Çizgi dolduysa otomatik eylemi çalıştır
        if progress >= 1.0:
            self._cancel_auto_execute_timer()
            if self._filtered_actions and 0 <= self._selected_index < len(self._filtered_actions):
                target_action = self._filtered_actions[self._selected_index]
                logger.info(
                    "Dolum çizgisi tamamlandı (%.1f sn). Eylem yürütülüyor: %s",
                    self.auto_execute_delay_sec,
                    target_action.get("title", "")
                )
                self._execute_and_close(target_action)
            return

        # 20 ms sonra sonraki kareyi çiz (50 FPS)
        self._auto_exec_timer_id = self.root.after(20, self._animate_progress_tick)

    def _refresh_action_list(self) -> None:
        """Öneri listesini arayüzde yeniden çizer."""
        query = self.entry_var.get()
        self._filtered_actions = self.registry.filter_actions(query)

        # Önceki etiketleri temizle
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        if not self._filtered_actions:
            lbl = tk.Label(
                self.list_frame,
                text="Eşleşen komut bulunamadı.",
                bg=self.theme.get("bg_color", "#181825"),
                fg=self.theme.get("placeholder_color", "#6c7086"),
                font=("Segoe UI", 11)
            )
            lbl.pack(pady=12)
            return

        # En fazla 6 öneri göster
        max_items = min(len(self._filtered_actions), 6)
        for i in range(max_items):
            action = self._filtered_actions[i]
            is_selected = (i == self._selected_index)

            bg = self.theme.get("selected_bg", "#45475a") if is_selected else self.theme.get("bg_color", "#181825")
            item_frame = tk.Frame(self.list_frame, bg=bg, padx=12, pady=6)
            item_frame.pack(fill=tk.X, pady=2)

            # Sayı Kodu Rozeti
            code_lbl = tk.Label(
                item_frame,
                text=f" {action.get('code', '')} ",
                bg=self.theme.get("accent_color", "#89b4fa"),
                fg="#11111b",
                font=("Segoe UI", 10, "bold")
            )
            code_lbl.pack(side=tk.LEFT, padx=(0, 10))

            # Başlık ve Açıklama
            title_text = f"{action.get('title', '')} — {action.get('description', '')}"
            text_lbl = tk.Label(
                item_frame,
                text=title_text,
                bg=bg,
                fg=self.theme.get("text_color", "#cdd6f4"),
                font=("Segoe UI", 11)
            )
            text_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Tıklama desteği
            idx = i
            item_frame.bind("<Button-1>", lambda e, act=action: self._execute_and_close(act))
            text_lbl.bind("<Button-1>", lambda e, act=action: self._execute_and_close(act))

    def _on_arrow_down(self, event: Any) -> str:
        """Aşağı ok tuşuna basıldığında seçimi ilerletir."""
        if self._filtered_actions:
            self._selected_index = (self._selected_index + 1) % len(self._filtered_actions)
            self._refresh_action_list()
        return "break"

    def _on_arrow_up(self, event: Any) -> str:
        """Yukarı ok tuşuna basıldığında seçimi geriletir."""
        if self._filtered_actions:
            self._selected_index = (self._selected_index - 1) + len(self._filtered_actions)
            self._selected_index %= len(self._filtered_actions)
            self._refresh_action_list()
        return "break"

    def _on_enter_pressed(self, event: Any) -> str:
        """Enter basıldığında seçili eylemi çalıştırır."""
        if self._filtered_actions and 0 <= self._selected_index < len(self._filtered_actions):
            action = self._filtered_actions[self._selected_index]
            self._execute_and_close(action)
        return "break"

    def _execute_and_close(self, action: Dict[str, Any]) -> None:
        """Eylemi çalıştırır ve komut çubuğunu gizler."""
        self._cancel_auto_execute_timer()
        self.hide()
        result = self.registry.execute_action(action)
        if self.on_action_executed:
            self.on_action_executed(result)
