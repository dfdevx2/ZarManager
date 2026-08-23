# app.py

import sys
import tkinter as tk
from tkinter import ttk 
import customtkinter as ctk
import webbrowser
import threading
import os
import urllib.request
import json
import platform
import ssl
import subprocess
import locale
from pathlib import Path
from tkinter import filedialog, messagebox
from config import ConfigManager
import locales
from core import ZarManagerCore

APP_VERSION = "v2.0.2"
GITHUB_REPO_API = "https://api.github.com/repos/dfdevx2/ZarManager/releases/latest"
GITHUB_REPO_URL = "https://github.com/dfdevx2/ZarManager"

class ToolTip:
    def __init__(self, widget, text_callback):
        self.widget = widget
        self.text_callback = text_callback
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(600, self.show)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def show(self):
        self.unschedule()
        if not self.tooltip_window:
            x, y, cx, cy = self.widget.bbox("insert")
            x = x + self.widget.winfo_rootx() + 25
            y = y + cy + self.widget.winfo_rooty() + 25
            
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            
            texto_dinamico = self.text_callback()
            label = tk.Label(self.tooltip_window, text=texto_dinamico, justify='left',
                             background="#1a1a1a", foreground="#ffffff", 
                             relief='flat', borderwidth=1, highlightbackground="#3B8ED0", highlightthickness=1,
                             font=("Segoe UI", 11, "normal"), padx=8, pady=6)
            label.pack(ipadx=1)
            
    def hide(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ==========================================
# TEMA: AMOLED ROXO E OUTROS
# ==========================================
THEME_COLORS = {
    "Sistema": {"mode": "System", "sidebar": ("gray85", "gray17"), "accent": ("#3B8ED0", "#1F6AA5"), "hover": ("#36719F", "#144870"), "text": ("black", "white")},
    "Branco": {"mode": "Light", "sidebar": ("#EBEBEB", "#EBEBEB"), "accent": ("#3B8ED0", "#3B8ED0"), "hover": ("#36719F", "#36719F"), "text": "black"},
    "Preto": {"mode": "Dark", "sidebar": ("#000000", "#050505"), "accent": ("#8A2BE2", "#6A0DAD"), "hover": ("#9932CC", "#4B0082"), "text": "white"},
    "Steam": {"mode": "Dark", "sidebar": ("#171a21", "#171a21"), "accent": ("#2a475e", "#2a475e"), "hover": ("#66c0f4", "#66c0f4"), "text": "white"},
    "Xbox": {"mode": "Dark", "sidebar": ("#121e13", "#121e13"), "accent": ("#107C10", "#107C10"), "hover": ("#0B580B", "#0B580B"), "text": "white"}
}

class ZarManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        if platform.system() == "Linux":
            ctk.set_window_scaling(1.1)
            ctk.set_widget_scaling(1.1)
            
        # ===================================================
        # GESTOR DE CONFIG (PRODUÇÃO VS DESENVOLVIMENTO)
        # ===================================================
        if getattr(sys, 'frozen', False):
            self.cfg = ConfigManager()
        else:
            class DevConfig:
                def __init__(self):
                    self.mem = {"workers": 4, "auto_update": True, "source_dir": "", "target_dir": ""}
                def get(self, key, default=""): 
                    val = self.mem.get(key, default)
                    return "" if val is None else val
                def set(self, key, value): 
                    self.mem[key] = value
            self.cfg = DevConfig()
            print("\n[DEV MODE ATIVO] O ZarManager está a rodar na RAM. Nenhuma config será guardada.\n")
            
        self.title(f"ZarManager {APP_VERSION}")
        self.minsize(950, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.resolve()
            if platform.system() == "Windows" and (base_path / "img" / "icon.ico").exists():
                self.iconbitmap(str(base_path / "img" / "icon.ico"))
        except Exception: pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.tab_data = {
            "auto": {"treeview": None, "items": [], "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}},
            "extract_arc": {"treeview": None, "items": [], "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}},
            "extract": {"treeview": None, "items": [], "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}},
            "compress": {"treeview": None, "items": [], "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}}
        }
        
        self.current_frame_name = "auto"
        
        # O SISTEMA DE ARRANQUE À PROVA DE SEGFAULTS
        if not self.cfg.get("first_boot_done"):
            self._build_first_boot_ui()
        else:
            self.build_all()
            self._apply_saved_geometry()
            self.after(200, self._force_render_refresh)
            self.after(2000, self.check_for_updates_silently)

    def _apply_saved_geometry(self):
        saved_geometry = self.cfg.get("window_geometry")
        if saved_geometry:
            self.geometry(saved_geometry)
        else:
            w, h = 1200, 800
            x = (self.winfo_screenwidth() // 2) - (w // 2)
            y = (self.winfo_screenheight() // 2) - (h // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_first_boot_ui(self):
        """Constrói a interface de Boas-vindas DENTRO da janela principal. Sem Toplevels, sem Segfaults."""
        try:
            sys_lang = locale.getdefaultlocale()[0] or "en"
            self.cfg.set("language", "pt-br" if sys_lang.lower().startswith("pt") else "en")
        except:
            self.cfg.set("language", "en")
            
        if not self.cfg.get("theme"):
            self.cfg.set("theme", "Sistema")
            
        self._apply_saved_geometry()
        
        setup_frame = ctk.CTkFrame(self, fg_color="transparent")
        setup_frame.grid(row=0, column=0, columnspan=2)
        
        ctk.CTkLabel(setup_frame, text="Bem-vindo / Welcome", font=("Segoe UI", 36, "bold")).pack(pady=(0, 10))
        ctk.CTkLabel(setup_frame, text="Escolha o tema inicial / Choose a starting theme:", font=("Segoe UI", 16)).pack(pady=(0, 40))
        
        self.temp_theme_var = ctk.StringVar(value=self.cfg.get("theme"))
        
        themes_frame = ctk.CTkFrame(setup_frame, fg_color="transparent")
        themes_frame.pack(pady=5)
        
        row, col = 0, 0
        for theme_name, colors in THEME_COLORS.items():
            accent = colors["accent"][1] if isinstance(colors["accent"], tuple) else colors["accent"]
            bg = colors["sidebar"][1] if isinstance(colors["sidebar"], tuple) else colors["sidebar"]
            
            frame_item = ctk.CTkFrame(themes_frame, fg_color="transparent")
            frame_item.grid(row=row, column=col, padx=20, pady=15, sticky="w")
            
            rb = ctk.CTkRadioButton(frame_item, text=theme_name, variable=self.temp_theme_var, value=theme_name, 
                                    fg_color=accent, text_color=accent, font=("Segoe UI", 15, "bold"))
            rb.pack(side="left")
            
            color_box = ctk.CTkFrame(frame_item, width=26, height=26, fg_color=bg, border_width=2, border_color=accent)
            color_box.pack(side="left", padx=(10, 0))
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        def on_finish():
            self.cfg.set("theme", self.temp_theme_var.get())
            self.cfg.set("first_boot_done", True)
            
            # Destrói o ecrã de setup e constrói a aplicação no mesmo canvas
            for widget in self.winfo_children():
                widget.destroy()
                
            self.build_all()
            self._apply_saved_geometry()
            self.after(200, self._force_render_refresh)
            self.after(2000, self.check_for_updates_silently)
            
        ctk.CTkButton(setup_frame, text="Continuar / Continue", command=on_finish, height=45, font=("Segoe UI", 16, "bold")).pack(pady=40)

    def _force_render_refresh(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 100 and h > 100:
            self.geometry(f"{w}x{h+1}")
            self.update_idletasks()
            self.after(50, lambda: self.geometry(f"{w}x{h}"))
        else:
            self.after(100, self._force_render_refresh)

    def on_closing(self):
        try: self.cfg.set("window_geometry", self.geometry())
        except Exception: pass
        for mode in ["auto", "extract_arc", "extract", "compress"]:
            if self.tab_data[mode].get("core_instance"):
                try: self.tab_data[mode]["core_instance"].request_cancel()
                except Exception: pass
        self.destroy()
        os._exit(0) 

    def play_sound(self, sound_type="success"):
        def _play():
            try:
                if platform.system() == "Windows":
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK if sound_type == "success" else winsound.MB_ICONHAND)
                else: self.bell() 
            except Exception: pass
        threading.Thread(target=_play, daemon=True).start()

    def open_browser(self, url):
        def _open():
            try:
                if platform.system() == "Linux": subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else: webbrowser.open_new(url)
            except Exception:
                try: webbrowser.open_new(url)
                except: self.log_message(f"[ERRO] Copie manualmente: {url}")
        threading.Thread(target=_open, daemon=True).start()

    def get_text(self, key: str): return locales.get_text(self.cfg.get("language"), key)

    def apply_appearance(self):
        theme_name = self.cfg.get("theme")
        self.theme_data = THEME_COLORS.get(theme_name, THEME_COLORS["Sistema"])
        ctk.set_appearance_mode(self.theme_data["mode"])
        
        bg_col = "#000000" if theme_name == "Preto" else ("#1a1a1a" if ctk.get_appearance_mode() == "Dark" else "#fcfcfc")
        fg_col = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", 
                        background=bg_col, 
                        foreground=fg_col, 
                        fieldbackground=bg_col, 
                        rowheight=35,
                        borderwidth=0, 
                        font=("Segoe UI", 12))
        style.map("Treeview", 
                  background=[("selected", self.theme_data["accent"][1])], 
                  foreground=[("selected", "white")])
        style.configure("Treeview.Heading", borderwidth=0)

    def build_all(self):
        self.apply_appearance()
        self.title(f"{self.get_text('app_title')} {APP_VERSION}")
        self._build_sidebar()
        self._build_main_area()
        self._build_frames()
        self.select_frame_by_name(self.current_frame_name)
        
        self.after(50, lambda: self.populate_file_list("auto", self.cfg.get("source_dir")))
        self.after(100, lambda: self.populate_file_list("extract_arc", self.cfg.get("source_dir")))
        self.after(150, lambda: self.populate_file_list("extract", self.cfg.get("source_dir")))
        self.after(200, lambda: self.populate_file_list("compress", self.cfg.get("source_dir")))

    def refresh_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        self.build_all()

    def select_folder(self, config_key: str, entry_widget: ctk.CTkEntry, mode_tab: str = None):
        folder = filedialog.askdirectory(initialdir=self.cfg.get(config_key) or "/")
        if folder:
            self.cfg.set(config_key, folder)
            entry_widget.delete(0, "end")
            entry_widget.insert(0, folder)
            self.log_message(f"[SISTEMA] {config_key} atualizado: {folder}")
            if config_key == "source_dir" and mode_tab:
                self.populate_file_list(mode_tab, folder)

    def populate_file_list(self, mode: str, directory: str):
        tv = self.tab_data[mode]["treeview"]
        if not tv or not directory or not os.path.exists(directory): return
            
        tv.delete(*tv.get_children())
        self.tab_data[mode]["items"].clear()
        
        target = Path(directory)
        items = []
        try:
            if mode == "auto": 
                for f in target.iterdir():
                    if (f.is_file() and f.suffix.lower() in ('.iso', '.zip', '.rar', '.7z', '.tar', '.gz')) or f.is_dir(): items.append(f)
            elif mode == "extract_arc":
                for f in target.iterdir():
                    if f.is_file() and f.suffix.lower() in ('.zip', '.rar', '.7z', '.tar', '.gz'): items.append(f)
            elif mode == "extract":
                items = list(target.glob("*.iso"))
            elif mode == "compress": 
                items = [d for d in target.iterdir() if d.is_dir()]
        except Exception: pass

        items = sorted(items)
        if not items:
            tv.insert("", "end", text="   Nenhum arquivo compatível encontrado na pasta.")
            return

        for item in items:
            tv.insert("", "end", iid=str(item), text=f"   {item.name}")
            self.tab_data[mode]["items"].append(item)
            
        tv.selection_set(tv.get_children())

    def toggle_all_selections(self, mode: str):
        tv = self.tab_data[mode]["treeview"]
        all_items = tv.get_children()
        if not all_items: return
        if len(tv.selection()) == len(all_items):
            tv.selection_remove(all_items)
        else:
            tv.selection_add(all_items)

    def start_process(self, mode: str):
        target = self.cfg.get("target_dir")
        if not target: return self.log_message("[ERRO] Diretório destino ausente.")

        selected_iids = self.tab_data[mode]["treeview"].selection()
        if not selected_iids: return self.log_message("[ERRO] Selecione ao menos um item.")
        
        selected_items = list(selected_iids)

        target_path = Path(target)
        collisions = []
        for p in selected_items:
            path = Path(p)
            name = path.stem if path.is_file() else path.name
            out = target_path / f"{name}.zar" if mode in ["auto", "compress"] else target_path / name
            if out.exists(): collisions.append(p)

        if collisions:
            resp = messagebox.askyesnocancel(title=self.get_text("msg_collision_title"), message=self.get_text("msg_collision_desc"))
            if resp is None: return self.log_message("[AVISO] Abortado (Conflito).")
            elif resp is False: 
                selected_items = [i for i in selected_items if i not in collisions]
                if not selected_items: return self.log_message("[AVISO] Fila vazia após pular conflitos.")
                self.log_message(f"[AVISO] Pulando {len(collisions)} itens.")

        keep_originals = messagebox.askyesno(
            title=self.get_text("delete_title"), 
            message=self.get_text("delete_msg")
        )

        self.tab_data[mode]["btns"]["start"].configure(state="disabled")
        self.tab_data[mode]["btns"]["pause"].configure(state="normal", text="Pausar Fila")
        self.tab_data[mode]["btns"]["cancel"].configure(state="normal")
        self.tab_data[mode]["progress"].set(0)
        self.tab_data[mode]["lbl_percentage"].configure(text="0%")
        self.log_message(f"[SISTEMA] Lote ({mode.upper()}) iniciado. Manter originais: {keep_originals}")
        
        threading.Thread(target=self._run_core_logic, args=(selected_items, target, self.cfg.get("workers"), mode, keep_originals), daemon=True).start()

    def _run_core_logic(self, items, target, workers, mode, keep_originals):
        manager = ZarManagerCore(items, target, workers, mode, keep_originals, lambda m: self.after(0, self.log_message, m),
                                 lambda c, t, r: self.after(0, self._update_prog, mode, c, t, r),
                                 lambda i, s: self.after(0, self._update_status, mode, i, s))
        self.tab_data[mode]["core_instance"] = manager
        try:
            if manager.verify_environment(): manager.start_processing()
        finally: self.after(0, self._reset_ui_controls, mode)

    def _reset_ui_controls(self, m):
        self.tab_data[m]["btns"]["start"].configure(state="normal")
        self.tab_data[m]["btns"]["pause"].configure(state="disabled", text="Pausar Fila")
        self.tab_data[m]["btns"]["cancel"].configure(state="disabled")

    def _update_prog(self, m, c, t, r):
        self.tab_data[m]["progress"].set(r)
        self.tab_data[m]["lbl_percentage"].configure(text=f"{int(r * 100)}%")
        self.tab_data[m]["lbl_counter"].configure(text=f"{c} / {t} concluídos")
        if c == t and t > 0: self.play_sound("success")

    def _update_status(self, m, item, status):
        if "FALHA" in status.upper(): self.play_sound("error")
        tasks = self.tab_data[m]["active_tasks"]
        frame = self.tab_data[m]["tasks_frame"]
        
        if status in ["CONCLUIDO", "FALHA", "FALHA CRÍTICA", "CANCELADO"]:
            if item in tasks: tasks.pop(item).destroy()
        else:
            if item not in tasks:
                lbl = ctk.CTkLabel(frame, text=f"• {item}: {status}", font=("Segoe UI", 13, "bold"), text_color=self.theme_data["accent"])
                lbl.pack(anchor="w", padx=15, pady=4)
                tasks[item] = lbl
            else: 
                tasks[item].configure(text=f"• {item}: {status}")

    def _build_sidebar(self):
        txt_color = self.theme_data["text"]
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.theme_data["sidebar"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) 
        
        ctk.CTkLabel(self.sidebar_frame, text="ZarManager", font=("", 24, "bold"), text_color=self.theme_data["text"]).grid(row=0, column=0, pady=30)
        
        self.btns = {}
        for mode, lang, r in [("auto", "tab_auto", 1), ("extract_arc", "tab_extract_arc", 2), 
                              ("extract", "tab_extract", 3), ("compress", "tab_compress", 4)]:
            b = ctk.CTkButton(self.sidebar_frame, text=self.get_text(lang), anchor="w", text_color=self.theme_data["text"], command=lambda m=mode: self.select_frame_by_name(m))
            b.grid(row=r, column=0, padx=20, pady=10, sticky="ew")
            ToolTip(b, lambda lg=f"tip_{mode}": self.get_text(lg))
            self.btns[mode] = b
            
        for mode, lang, r in [("settings", "tab_settings", 7), ("about", "tab_about", 8)]:
            b = ctk.CTkButton(self.sidebar_frame, text=self.get_text(lang), anchor="w", text_color=self.theme_data["text"], command=lambda m=mode: self.select_frame_by_name(m))
            b.grid(row=r, column=0, padx=20, pady=10, sticky="ew")
            self.btns[mode] = b

    def _build_main_area(self):
        mc = ctk.CTkFrame(self, fg_color="transparent")
        mc.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        mc.grid_rowconfigure(0, weight=3) 
        mc.grid_rowconfigure(1, weight=1) 
        mc.grid_columnconfigure(0, weight=1)
        
        self.view_container = ctk.CTkFrame(mc, corner_radius=10)
        self.view_container.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        
        cf = ctk.CTkFrame(mc, corner_radius=10)
        cf.grid(row=1, column=0, sticky="nsew")
        cf.grid_rowconfigure(0, weight=1)
        cf.grid_columnconfigure(0, weight=1)
        self.console_textbox = ctk.CTkTextbox(cf, font=("Monospace", 13))
        self.console_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.log_message(self.get_text("log_ready"))

    def log_message(self, message: str):
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", message + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def _build_frames(self):
        self.frames = {n: ctk.CTkFrame(self.view_container, fg_color="transparent") for n in self.btns.keys()}
        for f in self.frames.values(): f.grid(row=0, column=0, sticky="nsew")

        self._build_action_tab(self.frames["auto"], "tab_auto", "Full Pipeline: Descompacta, Extrai XISO e Comprime ZAR.", "auto")
        self._build_action_tab(self.frames["extract_arc"], "tab_extract_arc", "Apenas extrai de forma plana Arquivos ZIP, RAR e 7Z.", "extract_arc")
        self._build_action_tab(self.frames["extract"], "tab_extract", "Apenas extrai arquivos de uma imagem .ISO.", "extract")
        self._build_action_tab(self.frames["compress"], "tab_compress", "Apenas compacta uma pasta estruturada em .zar.", "compress")
        self._populate_settings_frame(self.frames["settings"])
        self._populate_about_frame(self.frames["about"])

    def _build_action_tab(self, frame, title_key: str, description: str, mode: str):
        frame.grid_rowconfigure(2, weight=1) 
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text=self.get_text(title_key), font=("", 24, "bold")).grid(row=0, column=0, sticky="w", padx=30, pady=(30, 5))
        ctk.CTkLabel(frame, text=description, text_color="gray").grid(row=1, column=0, sticky="w", padx=30, pady=(0, 15))

        sel_frame = ctk.CTkFrame(frame, fg_color="transparent")
        sel_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=5)
        
        sel_frame.grid_rowconfigure(2, weight=1)
        sel_frame.grid_columnconfigure(0, weight=1)

        dir_frame = ctk.CTkFrame(sel_frame, fg_color="transparent")
        dir_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        for k in ["source", "target"]:
            ctk.CTkLabel(dir_frame, text=self.get_text(f"lbl_{k}"), font=("", 12, "bold")).pack(anchor="w")
            f = ctk.CTkFrame(dir_frame, fg_color="transparent")
            f.pack(fill="x", pady=(0, 15))
            e = ctk.CTkEntry(f)
            e.pack(side="left", fill="x", expand=True, padx=(0, 10))
            e.insert(0, self.cfg.get(f"{k}_dir"))
            ctk.CTkButton(f, text="Browse", width=100, command=lambda ky=f"{k}_dir", ey=e: self.select_folder(ky, ey, mode)).pack(side="right")

        ctk.CTkLabel(sel_frame, text="Itens Identificados:", font=("", 12, "bold")).grid(row=1, column=0, sticky="sw", pady=(0,5))
        ctk.CTkButton(sel_frame, text="Inverter Seleção", width=120, fg_color="gray", command=lambda: self.toggle_all_selections(mode)).grid(row=1, column=1, sticky="se", pady=(0,5))
        
        lb_frame = ctk.CTkFrame(sel_frame)
        lb_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        lb_frame.grid_rowconfigure(0, weight=1)
        lb_frame.grid_columnconfigure(0, weight=1)
        
        tv = ttk.Treeview(lb_frame, selectmode="extended", show="tree")
        tv.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=2)
        
        sb = ctk.CTkScrollbar(lb_frame, command=tv.yview)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=2)
        
        tv.configure(yscrollcommand=sb.set)
        
        self.tab_data[mode]["treeview"] = tv

        bot_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bot_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=15)
        bot_frame.grid_columnconfigure(0, weight=1)

        self.tab_data[mode]["tasks_frame"] = ctk.CTkFrame(bot_frame, fg_color=("gray85", "gray15"), corner_radius=5)
        self.tab_data[mode]["tasks_frame"].grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        info_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew")
        
        self.tab_data[mode]["lbl_counter"] = ctk.CTkLabel(info_frame, text="0/0", font=("", 12, "bold"))
        self.tab_data[mode]["lbl_counter"].pack(side="left")
        self.tab_data[mode]["lbl_percentage"] = ctk.CTkLabel(info_frame, text="0%", font=("", 12, "bold"))
        self.tab_data[mode]["lbl_percentage"].pack(side="right")

        self.tab_data[mode]["progress"] = ctk.CTkProgressBar(bot_frame, progress_color=self.theme_data["accent"], height=22, corner_radius=8)
        self.tab_data[mode]["progress"].grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.tab_data[mode]["progress"].set(0)

        ctrl_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        ctrl_frame.grid(row=2, column=1, sticky="e", padx=15)
        
        btn_start = ctk.CTkButton(ctrl_frame, text="Iniciar Lote", height=35, font=ctk.CTkFont(weight="bold"), fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white", command=lambda m=mode: self.start_process(m))
        btn_start.pack(side="left", padx=(0, 10))
        btn_pause = ctk.CTkButton(ctrl_frame, text="Pausar Fila", height=35, font=ctk.CTkFont(weight="bold"), fg_color="gray", hover_color="darkgray", state="disabled", command=lambda m=mode: self.tab_data[mode]["core_instance"].toggle_pause())
        btn_pause.pack(side="left", padx=(0, 10))
        btn_cancel = ctk.CTkButton(ctrl_frame, text="Cancelar Operação", height=35, font=ctk.CTkFont(weight="bold"), fg_color="#8B0000", hover_color="#660000", text_color="white", state="disabled", command=lambda m=mode: self.tab_data[mode]["core_instance"].request_cancel())
        btn_cancel.pack(side="left")
        
        self.tab_data[mode]["btns"] = {"start": btn_start, "pause": btn_pause, "cancel": btn_cancel}

    def _populate_settings_frame(self, frame):
        ctk.CTkLabel(frame, text=self.get_text("tab_settings"), font=("", 24, "bold")).pack(anchor="w", padx=30, pady=30)

        self.lang_var = ctk.StringVar(value=self.cfg.get("language"))
        ctk.CTkComboBox(frame, variable=self.lang_var, values=["pt-br", "en"], command=self.on_setting_change).pack(anchor="w", padx=30, pady=10)

        self.theme_var = ctk.StringVar(value=self.cfg.get("theme"))
        ctk.CTkComboBox(frame, variable=self.theme_var, values=["Sistema", "Preto", "Branco", "Steam", "Xbox"], command=self.on_setting_change).pack(anchor="w", padx=30, pady=10)

        ctk.CTkLabel(frame, text=f'{self.get_text("lbl_workers")} (Atual: {self.cfg.get("workers")})').pack(anchor="w", padx=30, pady=(10, 0))
        slider = ctk.CTkSlider(frame, from_=1, to=16, number_of_steps=15, command=self.on_worker_slider_change)
        slider.set(self.cfg.get("workers"))
        slider.pack(anchor="w", padx=30, pady=5)
        
        ctk.CTkLabel(frame, text=self.get_text("worker_warning"), text_color="orange", justify="left").pack(anchor="w", padx=30, pady=(20, 20))

    def _populate_about_frame(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)

        ctk.CTkLabel(center_frame, text="ZarManager", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(center_frame, text=f"Versão Atual: {APP_VERSION}", font=("Segoe UI", 14, "italic"), text_color="gray").pack(anchor="w", pady=(0, 20))
        
        fr_tut = ctk.CTkFrame(center_frame, fg_color=("gray85", "gray15"), corner_radius=10)
        fr_tut.pack(fill="x", pady=10)
        ctk.CTkLabel(fr_tut, text=self.get_text("about_tutorial"), justify="left", font=("Segoe UI", 13)).pack(padx=20, pady=20, anchor="w")
        
        info_box = ctk.CTkFrame(center_frame, fg_color="transparent")
        info_box.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_box, text="💻 Desenvolvedor: dfdevx2", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=2)
        ctk.CTkLabel(info_box, text="📜 Licença: MIT License", font=("Segoe UI", 13)).pack(anchor="w", pady=2)
        
        link_lbl = ctk.CTkLabel(info_box, text="🌐 Repositório Oficial no GitHub", font=("Segoe UI", 13, "bold", "underline"), text_color="#3B8ED0", cursor="hand2")
        link_lbl.pack(anchor="w", pady=2)
        link_lbl.bind("<Button-1>", lambda e: self.open_browser(GITHUB_REPO_URL))

        updates_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        updates_frame.pack(fill="x", pady=(30, 10))

        auto_val = self.cfg.get("auto_update")
        if auto_val is None:
            auto_val = True
            self.cfg.set("auto_update", True)
            
        self.auto_update_var = ctk.BooleanVar(value=auto_val)
        switch_auto = ctk.CTkSwitch(updates_frame, text=self.get_text("lbl_auto_update"), variable=self.auto_update_var, command=self.on_auto_update_change, font=("Segoe UI", 12, "bold"))
        switch_auto.pack(side="left", padx=(0, 20))
        
        self.btn_check_update = ctk.CTkButton(updates_frame, text=self.get_text("btn_check_update"), fg_color="gray", command=self.check_for_updates)
        self.btn_check_update.pack(side="left")
        
        self.lbl_update_status = ctk.CTkLabel(updates_frame, text="", font=("Segoe UI", 12, "italic"))
        self.lbl_update_status.pack(side="left", padx=20)
        
        self.btn_download_update = ctk.CTkButton(center_frame, text=self.get_text("btn_download_update"), fg_color="#107C10", text_color="white")

    def check_for_updates(self):
        self.btn_check_update.configure(state="disabled")
        self.lbl_update_status.configure(text="Procurando...", text_color="gray")
        self.btn_download_update.pack_forget()
        threading.Thread(target=self._check_for_updates_thread, daemon=True).start()

    def check_for_updates_silently(self):
        if not self.cfg.get("auto_update"): return
        threading.Thread(target=self._silent_update_thread, daemon=True).start()

    def _silent_update_thread(self):
        try:
            req = urllib.request.Request(GITHUB_REPO_API, headers={'User-Agent': 'ZarManager'})
            with urllib.request.urlopen(req, timeout=7, context=ssl._create_unverified_context()) as res:
                data = json.loads(res.read().decode())
                if data.get("tag_name") not in ["", APP_VERSION]:
                    self.after(0, lambda: self._show_update_popup(data.get("tag_name"), data.get("html_url")))
        except Exception: pass 

    def _show_update_popup(self, v, url):
        if messagebox.askyesno(title=self.get_text("msg_update_popup_title"), message=self.get_text("msg_update_popup_desc").format(v)):
            self.open_browser(url)

    def _check_for_updates_thread(self):
        try:
            req = urllib.request.Request(GITHUB_REPO_API, headers={'User-Agent': 'ZarManager'})
            with urllib.request.urlopen(req, timeout=7, context=ssl._create_unverified_context()) as res:
                data = json.loads(res.read().decode())
                v = data.get("tag_name", "")
                if v and v != APP_VERSION:
                    self.after(0, lambda: self._update_ui_update_found(self.get_text("msg_update_avail").format(v), data.get("html_url")))
                else:
                    self.after(0, lambda: self._update_ui_update_none(self.get_text("msg_update_latest").format(APP_VERSION)))
        except Exception as e:
            self.after(0, lambda: self._update_ui_update_error(str(e)))

    def _update_ui_update_found(self, msg, url):
        self.btn_check_update.configure(state="normal")
        self.lbl_update_status.configure(text=msg, text_color="green")
        self.btn_download_update.configure(command=lambda: self.open_browser(url))
        self.btn_download_update.pack(anchor="w", pady=10)

    def _update_ui_update_none(self, msg):
        self.btn_check_update.configure(state="normal")
        self.lbl_update_status.configure(text=msg, text_color="gray")

    def _update_ui_update_error(self, err):
        self.btn_check_update.configure(state="normal")
        self.lbl_update_status.configure(text="Falha de rede.", text_color="red")

    def select_frame_by_name(self, name: str):
        self.current_frame_name = name
        for btn_name, btn in self.btns.items():
            btn.configure(fg_color=self.theme_data["accent"] if btn_name == name else "transparent", 
                          text_color="white" if btn_name == name else self.theme_data["text"])
        self.frames[name].tkraise()
        
        if name in ["auto", "extract_arc", "extract", "compress"]:
            if not self.tab_data[name]["items"] and self.cfg.get("source_dir"):
                self.populate_file_list(name, self.cfg.get("source_dir"))

    def on_setting_change(self, choice):
        self.cfg.set("language", self.lang_var.get())
        self.cfg.set("theme", self.theme_var.get())
        self.refresh_ui()

    def on_worker_slider_change(self, value):
        self.cfg.set("workers", int(value))

    def on_auto_update_change(self):
        self.cfg.set("auto_update", self.auto_update_var.get())

if __name__ == "__main__":
    app = ZarManagerGUI()
    app.mainloop()