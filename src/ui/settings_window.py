"""Ayarlar penceresi grafik arayüz modülü.

Kullanıcının kısayolları (sayı kodları, başlık, tür ve komutlar) elle eklemesini,
düzenlemesini, silmesini ve sırasını değiştirmesini sağlayan modern bir ayarlar penceresi sunar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional
from src.config.config_manager import ConfigManager
from src.utils.logger import get_logger

logger = get_logger()


class SettingsWindow:
    """Num Launcher ayarlar ve kısayol yönetim penceresi."""

    def __init__(
        self,
        parent: tk.Tk,
        config_manager: ConfigManager,
        on_actions_updated: Optional[Callable[[List[Dict[str, Any]]], None]] = None
    ) -> None:
        """SettingsWindow sınıfını başlatır.

        Args:
            parent: Ana Tkinter penceresi.
            config_manager: Yapılandırma yöneticisi.
            on_actions_updated: Kısayollar güncellendiğinde çağrılan geribildirim fonksiyonu.
        """
        self.parent = parent
        self.config_manager = config_manager
        self.on_actions_updated = on_actions_updated

        # Yapılandırmadan mevcut eylemlerin bir kopyasını al
        self.actions: List[Dict[str, Any]] = [dict(a) for a in self.config_manager.get_actions()]
        self.editing_index: Optional[int] = None

        self.window: Optional[tk.Toplevel] = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Ayarlar penceresini ve bileşenlerini oluşturur."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Num Launcher — Kısayol Ayarları")
        self.window.geometry("780x560")
        self.window.minsize(680, 480)
        self.window.configure(bg="#181825")
        self.window.attributes("-topmost", True)

        # Başlık ve Açıklama Çerçevesi
        header_frame = tk.Frame(self.window, bg="#181825", padx=20, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="⚙️ Kısayol ve Eylem Ayarları",
            bg="#181825",
            fg="#cdd6f4",
            font=("Segoe UI", 14, "bold")
        )
        title_lbl.pack(anchor=tk.W)

        desc_lbl = tk.Label(
            header_frame,
            text="Kısayolları elle ekleyin, silin, düzenleyin veya ok butonlarıyla sırasını değiştirin.",
            bg="#181825",
            fg="#a6adc8",
            font=("Segoe UI", 10)
        )
        desc_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Ana içerik alanı (Sol: Liste ve Sıralama, Sağ/Alt: Düzenleme Formu)
        content_frame = tk.Frame(self.window, bg="#181825", padx=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Tablo Çerçevesi
        table_container = tk.Frame(content_frame, bg="#1e1e2e", highlightbackground="#313244", highlightthickness=1)
        table_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Treeview (Kısayol Listesi)
        columns = ("order", "code", "title", "type", "command")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8
        )

        # Başlıklar
        self.tree.heading("order", text="#")
        self.tree.heading("code", text="Sayı / Kod")
        self.tree.heading("title", text="Başlık")
        self.tree.heading("type", text="Tür")
        self.tree.heading("command", text="Komut / URL")

        # Sütun Genişlikleri
        self.tree.column("order", width=40, anchor=tk.CENTER)
        self.tree.column("code", width=80, anchor=tk.CENTER)
        self.tree.column("title", width=180, anchor=tk.W)
        self.tree.column("type", width=70, anchor=tk.CENTER)
        self.tree.column("command", width=340, anchor=tk.W)

        # Kaydırma Çubuğu
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_item_selected)

        # Sıralama ve İşlem Butonları Çubuğu
        actions_bar = tk.Frame(content_frame, bg="#181825", pady=8)
        actions_bar.pack(fill=tk.X)

        # Sıralama butonları (Sol taraf)
        btn_up = tk.Button(
            actions_bar,
            text="⬆️ Yukarı Taşı",
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#cdd6f4",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self._move_up
        )
        btn_up.pack(side=tk.LEFT, padx=(0, 6))

        btn_down = tk.Button(
            actions_bar,
            text="⬇️ Aşağı Taşı",
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#cdd6f4",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self._move_down
        )
        btn_down.pack(side=tk.LEFT, padx=(0, 12))

        # Sil butonu
        btn_delete = tk.Button(
            actions_bar,
            text="🗑️ Sil",
            bg="#f38ba8",
            fg="#11111b",
            activebackground="#eba0ac",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            font=("Segoe UI", 9, "bold"),
            command=self._delete_selected
        )
        btn_delete.pack(side=tk.LEFT)

        # Form Çerçevesi (Kısayol Ekle / Düzenle)
        form_frame = tk.LabelFrame(
            content_frame,
            text=" Kısayol Düzenleme / Ekleme ",
            bg="#181825",
            fg="#89b4fa",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8
        )
        form_frame.pack(fill=tk.X, pady=(6, 8))

        # Form Alanları (Grid)
        lbl_code = tk.Label(form_frame, text="Kod:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9))
        lbl_code.grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        self.entry_code = tk.Entry(form_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="#89b4fa", relief=tk.FLAT, width=8)
        self.entry_code.grid(row=0, column=1, sticky=tk.W, padx=4, pady=3)

        lbl_title = tk.Label(form_frame, text="Başlık:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9))
        lbl_title.grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        self.entry_title = tk.Entry(form_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="#89b4fa", relief=tk.FLAT, width=20)
        self.entry_title.grid(row=0, column=3, sticky=tk.W, padx=4, pady=3)

        lbl_type = tk.Label(form_frame, text="Tür:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9))
        lbl_type.grid(row=0, column=4, sticky=tk.W, padx=4, pady=3)
        self.type_var = tk.StringVar(value="cmd")
        self.combo_type = ttk.Combobox(form_frame, textvariable=self.type_var, values=["cmd", "url"], state="readonly", width=6)
        self.combo_type.grid(row=0, column=5, sticky=tk.W, padx=4, pady=3)

        lbl_desc = tk.Label(form_frame, text="Açıklama:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9))
        lbl_desc.grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        self.entry_desc = tk.Entry(form_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="#89b4fa", relief=tk.FLAT, width=32)
        self.entry_desc.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, padx=4, pady=3)

        lbl_cmd = tk.Label(form_frame, text="Komut / URL:", bg="#181825", fg="#cdd6f4", font=("Segoe UI", 9))
        lbl_cmd.grid(row=2, column=0, sticky=tk.W, padx=4, pady=3)
        self.entry_cmd = tk.Entry(form_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="#89b4fa", relief=tk.FLAT)
        self.entry_cmd.grid(row=2, column=1, columnspan=5, sticky=tk.W+tk.E, padx=4, pady=3)

        # Form Butonları
        form_btn_box = tk.Frame(form_frame, bg="#181825")
        form_btn_box.grid(row=3, column=0, columnspan=6, sticky=tk.E, pady=(6, 2))

        self.btn_save_form = tk.Button(
            form_btn_box,
            text="➕ Listeye Ekle",
            bg="#a6e3a1",
            fg="#11111b",
            activebackground="#94e2d5",
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=3,
            command=self._apply_form_to_list
        )
        self.btn_save_form.pack(side=tk.RIGHT, padx=4)

        btn_clear_form = tk.Button(
            form_btn_box,
            text="Formu Temizle",
            bg="#313244",
            fg="#cdd6f4",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self._clear_form
        )
        btn_clear_form.pack(side=tk.RIGHT, padx=4)

        # Alt Butonlar (Kaydet ve Kapat)
        bottom_bar = tk.Frame(self.window, bg="#181825", padx=20, pady=12)
        bottom_bar.pack(fill=tk.X)

        btn_commit = tk.Button(
            bottom_bar,
            text="💾 Değişiklikleri Kaydet",
            bg="#89b4fa",
            fg="#11111b",
            activebackground="#b4befe",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=6,
            command=self._save_and_close
        )
        btn_commit.pack(side=tk.RIGHT, padx=(8, 0))

        btn_close = tk.Button(
            bottom_bar,
            text="İptal / Kapat",
            bg="#313244",
            fg="#cdd6f4",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self.close
        )
        btn_close.pack(side=tk.RIGHT)

        # Kısayol Tuşları
        self.window.bind("<Escape>", lambda e: self.close())

        self._refresh_tree()

    def _refresh_tree(self) -> None:
        """Kısayol tablosunu günceller."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, act in enumerate(self.actions):
            self.tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(
                    i + 1,
                    act.get("code", ""),
                    act.get("title", ""),
                    act.get("type", "cmd"),
                    act.get("command", "")
                )
            )

    def _on_item_selected(self, event: Any) -> None:
        """Tablodan bir satır seçildiğinde form alanlarını doldurur."""
        selected = self.tree.selection()
        if not selected:
            return

        index = int(selected[0])
        if 0 <= index < len(self.actions):
            self.editing_index = index
            act = self.actions[index]
            self.entry_code.delete(0, tk.END)
            self.entry_code.insert(0, act.get("code", ""))

            self.entry_title.delete(0, tk.END)
            self.entry_title.insert(0, act.get("title", ""))

            self.entry_desc.delete(0, tk.END)
            self.entry_desc.insert(0, act.get("description", ""))

            self.type_var.set(act.get("type", "cmd"))

            self.entry_cmd.delete(0, tk.END)
            self.entry_cmd.insert(0, act.get("command", ""))

            self.btn_save_form.config(text="✏️ Güncelle", bg="#f9e2af")

    def _clear_form(self) -> None:
        """Formu temizler ve yeni ekleme moduna geçer."""
        self.editing_index = None
        self.entry_code.delete(0, tk.END)
        self.entry_title.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.type_var.set("cmd")
        self.entry_cmd.delete(0, tk.END)
        self.btn_save_form.config(text="➕ Listeye Ekle", bg="#a6e3a1")
        self.tree.selection_remove(self.tree.selection())

    def _apply_form_to_list(self) -> None:
        """Formdaki veriyi eylem listesine ekler veya günceller."""
        code = self.entry_code.get().strip()
        title = self.entry_title.get().strip()
        desc = self.entry_desc.get().strip()
        act_type = self.type_var.get().strip().lower()
        cmd = self.entry_cmd.get().strip()

        if not code or not title or not cmd:
            messagebox.showwarning("Eksik Bilgi", "Kod, Başlık ve Komut alanları boş bırakılamaz.")
            return

        action_data = {
            "code": code,
            "title": title,
            "description": desc,
            "type": act_type,
            "command": cmd
        }

        if self.editing_index is not None and 0 <= self.editing_index < len(self.actions):
            self.actions[self.editing_index] = action_data
            logger.info("Kısayol güncellendi: [%s] %s", code, title)
        else:
            self.actions.append(action_data)
            logger.info("Yeni kısayol eklendi: [%s] %s", code, title)

        self._refresh_tree()
        self._clear_form()

    def _delete_selected(self) -> None:
        """Seçili kısayolu listeden siler."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Seçim Yok", "Lütfen silmek istediğiniz kısayolu seçin.")
            return

        index = int(selected[0])
        if 0 <= index < len(self.actions):
            act = self.actions.pop(index)
            logger.info("Kısayol silindi: [%s] %s", act.get("code"), act.get("title"))
            self._refresh_tree()
            self._clear_form()

    def _move_up(self) -> None:
        """Seçili kısayolu bir üst sıraya taşır."""
        selected = self.tree.selection()
        if not selected:
            return

        index = int(selected[0])
        if index > 0:
            self.actions[index], self.actions[index - 1] = self.actions[index - 1], self.actions[index]
            self._refresh_tree()
            self.tree.selection_set(str(index - 1))

    def _move_down(self) -> None:
        """Seçili kısayolu bir alt sıraya taşır."""
        selected = self.tree.selection()
        if not selected:
            return

        index = int(selected[0])
        if index < len(self.actions) - 1:
            self.actions[index], self.actions[index + 1] = self.actions[index + 1], self.actions[index]
            self._refresh_tree()
            self.tree.selection_set(str(index + 1))

    def _save_and_close(self) -> None:
        """Değişiklikleri diske kaydeder ve pencereyi kapatır."""
        success = self.config_manager.set_actions(self.actions)
        if success:
            logger.info("Tüm kısayollar başarıyla kaydedildi. Toplam: %d", len(self.actions))
            if self.on_actions_updated:
                self.on_actions_updated(self.actions)
            messagebox.showinfo("Başarılı", "Kısayol ayarları başarıyla kaydedildi!")
            self.close()
        else:
            messagebox.showerror("Hata", "Kısayollar kaydedilirken hata oluştu!")

    def close(self) -> None:
        """Pencereyi kapatır."""
        if self.window:
            self.window.destroy()
            self.window = None
