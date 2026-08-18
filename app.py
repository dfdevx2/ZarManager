# app.py
# Interface Gráfica Definitiva - ZarManager v1.0 (Com Porcentagem e Geometria Fixa)

import customtkinter as ctk
import webbrowser
import threading
import os
from pathlib import Path
from tkinter import filedialog
from config import ConfigManager
import locales
from core import ZarManagerCore

THEME_COLORS = {
    "Sistema": {"mode": "System", "sidebar": ("gray85", "gray17"), "accent": ("#3B8ED0", "#1F6AA5"), "hover": ("#36719F", "#144870"), "text": ("black", "white")},
    "Branco": {"mode": "Light", "sidebar": ("#EBEBEB", "#EBEBEB"), "accent": ("#3B8ED0", "#3B8ED0"), "hover": ("#36719F", "#36719F"), "text": "black"},
    "Preto": {"mode": "Dark", "sidebar": ("gray13", "gray13"), "accent": ("#1F6AA5", "#1F6AA5"), "hover": ("#144870", "#144870"), "text": "white"},
    "Steam": {"mode": "Dark", "sidebar": ("#171a21", "#171a21"), "accent": ("#2a475e", "#2a475e"), "hover": ("#66c0f4", "#66c0f4"), "text": "white"},
    "Xbox": {"mode": "Dark", "sidebar": ("#121e13", "#121e13"), "accent": ("#107C10", "#107C10"), "hover": ("#0B580B", "#0B580B"), "text": "white"}
}

class ZarManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.cfg = ConfigManager()
        self.title("ZarManager")
        
        # Garante a abertura exata na proporção solicitada
        self.geometry("1150x800")
        self.minsize(1050, 750)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.tab_data = {
            "auto": {"checkboxes": {}, "scroll_frame": None, "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}},
            "extract": {"checkboxes": {}, "scroll_frame": None, "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}},
            "compress": {"checkboxes": {}, "scroll_frame": None, "lbl_counter": None, "lbl_percentage": None, "progress": None, "tasks_frame": None, "active_tasks": {}, "core_instance": None, "btns": {}}
        }
        
        self.current_frame_name = "auto"
        self.build_all()

    def get_text(self, key: str) -> str:
        return locales.get_text(self.cfg.get("language"), key)

    def apply_appearance(self):
        theme_name = self.cfg.get("theme")
        if theme_name not in THEME_COLORS: theme_name = "Sistema"
        self.theme_data = THEME_COLORS[theme_name]
        ctk.set_appearance_mode(self.theme_data["mode"])

    def build_all(self):
        self.apply_appearance()
        self.title(self.get_text("app_title"))
        self._build_sidebar()
        self._build_main_area()
        self._build_frames()
        self.select_frame_by_name(self.current_frame_name)
        
        self.populate_file_list("auto", self.cfg.get("source_dir"))
        self.populate_file_list("extract", self.cfg.get("source_dir"))
        self.populate_file_list("compress", self.cfg.get("source_dir"))

    def refresh_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        self.build_all()

    def select_folder(self, config_key: str, entry_widget: ctk.CTkEntry, mode_tab: str = None):
        current_path = self.cfg.get(config_key)
        selected_dir = filedialog.askdirectory(initialdir=current_path if current_path else "/")
        
        if selected_dir:
            self.cfg.set(config_key, selected_dir)
            entry_widget.delete(0, "end")
            entry_widget.insert(0, selected_dir)
            self.log_message(f"[SISTEMA] {config_key} atualizado para: {selected_dir}")
            
            if config_key == "source_dir" and mode_tab:
                self.populate_file_list("auto", selected_dir)
                self.populate_file_list("extract", selected_dir)
                self.populate_file_list("compress", selected_dir)

    def populate_file_list(self, mode: str, directory: str):
        scroll_frame = self.tab_data[mode]["scroll_frame"]
        if not scroll_frame or not directory or not os.path.exists(directory): return
            
        for widget in scroll_frame.winfo_children(): widget.destroy()
        self.tab_data[mode]["checkboxes"].clear()
        
        target_path = Path(directory)
        items_found = []
        
        try:
            if mode in ["auto", "extract"]: items_found = list(target_path.glob("*.iso"))
            elif mode == "compress": items_found = [d for d in target_path.iterdir() if d.is_dir()]
        except Exception: pass

        if not items_found:
            ctk.CTkLabel(scroll_frame, text="Nenhum item compatível encontrado na pasta.", text_color="gray").pack(pady=20)
            return

        for item in sorted(items_found):
            var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(scroll_frame, text=item.name, variable=var, fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"])
            chk.pack(anchor="w", padx=10, pady=5)
            self.tab_data[mode]["checkboxes"][str(item)] = var

    def toggle_all_selections(self, mode: str):
        checkboxes = self.tab_data[mode]["checkboxes"].values()
        if not checkboxes: return
        all_checked = all(var.get() for var in checkboxes)
        new_state = not all_checked
        for var in checkboxes: var.set(new_state)

    def start_process(self, mode: str):
        target = self.cfg.get("target_dir")
        workers = self.cfg.get("workers")
        
        if not target:
            self.log_message("[ERRO] Diretório de destino ausente.")
            return

        selected_items = [path for path, var in self.tab_data[mode]["checkboxes"].items() if var.get()]
        if not selected_items:
            self.log_message("[ERRO] Nenhum arquivo foi selecionado para processamento.")
            return

        self.tab_data[mode]["btns"]["start"].configure(state="disabled")
        self.tab_data[mode]["btns"]["pause"].configure(state="normal", text="Pausar Fila")
        self.tab_data[mode]["btns"]["cancel"].configure(state="normal")
        
        self.tab_data[mode]["progress"].set(0)
        self.tab_data[mode]["lbl_percentage"].configure(text="0%")
        self.tab_data[mode]["lbl_counter"].configure(text=f"0 / {len(selected_items)} itens concluídos")
        self.log_message(f"[SISTEMA] Acionando lote ({mode.upper()}) com {len(selected_items)} itens alocados...")
        
        process_thread = threading.Thread(target=self._run_core_logic, args=(selected_items, target, workers, mode), daemon=True)
        process_thread.start()

    def toggle_pause_process(self, mode: str):
        core = self.tab_data[mode].get("core_instance")
        if core:
            is_paused = core.toggle_pause()
            if is_paused:
                self.tab_data[mode]["btns"]["pause"].configure(text="Retomar Fila", fg_color="orange", hover_color="darkorange")
            else:
                self.tab_data[mode]["btns"]["pause"].configure(text="Pausar Fila", fg_color="gray", hover_color="darkgray")

    def cancel_process(self, mode: str):
        core = self.tab_data[mode].get("core_instance")
        if core:
            core.request_cancel()
            self.tab_data[mode]["btns"]["pause"].configure(state="disabled")
            self.tab_data[mode]["btns"]["cancel"].configure(state="disabled", text="Abortando...")

    def _run_core_logic(self, selected_items, target, workers, mode):
        manager = ZarManagerCore(
            selected_items=selected_items, target_directory=target, max_workers=workers, mode=mode,
            log_callback=self._update_log_from_thread,
            progress_callback=lambda current, total, ratio: self._update_progress_from_thread(mode, current, total, ratio),
            status_callback=lambda item, status: self._update_task_status_from_thread(mode, item, status)
        )
        self.tab_data[mode]["core_instance"] = manager
        
        try:
            if manager.verify_environment():
                manager.start_processing()
            else:
                self._update_log_from_thread("[ERRO CRÍTICO] Execução abortada devido à falha ambiental.")
        finally:
            self.after(0, lambda: self._reset_ui_controls(mode))

    def _reset_ui_controls(self, mode: str):
        self.tab_data[mode]["btns"]["start"].configure(state="normal")
        self.tab_data[mode]["btns"]["pause"].configure(state="disabled", text="Pausar Fila", fg_color="gray")
        self.tab_data[mode]["btns"]["cancel"].configure(state="disabled", text="Cancelar Operação")

    def _update_log_from_thread(self, message: str):
        self.after(0, lambda: self.log_message(message))

    def _update_progress_from_thread(self, mode: str, current: int, total: int, ratio: float):
        pct = int(ratio * 100)
        self.after(0, lambda: self.tab_data[mode]["progress"].set(ratio))
        self.after(0, lambda: self.tab_data[mode]["lbl_percentage"].configure(text=f"{pct}%"))
        self.after(0, lambda: self.tab_data[mode]["lbl_counter"].configure(text=f"{current} / {total} itens concluídos"))

    def _update_task_status_from_thread(self, mode: str, item_name: str, status: str):
        def update_ui():
            tasks_dict = self.tab_data[mode]["active_tasks"]
            frame = self.tab_data[mode]["tasks_frame"]
            
            if status in ["CONCLUIDO", "FALHA", "FALHA CRÍTICA", "CANCELADO"]:
                if item_name in tasks_dict:
                    tasks_dict[item_name].destroy()
                    del tasks_dict[item_name]
            else:
                if item_name not in tasks_dict:
                    lbl = ctk.CTkLabel(frame, text=f"• {item_name}: {status}", font=ctk.CTkFont(size=12, weight="bold"))
                    lbl.pack(anchor="w", padx=10, pady=2)
                    tasks_dict[item_name] = lbl
                else:
                    tasks_dict[item_name].configure(text=f"• {item_name}: {status}")
        self.after(0, update_ui)

    def _build_sidebar(self):
        txt_color = self.theme_data["text"]
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.theme_data["sidebar"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ZarManager", font=ctk.CTkFont(size=24, weight="bold"), text_color=txt_color)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))
        
        self.btn_auto = ctk.CTkButton(self.sidebar_frame, text=self.get_text("tab_auto"), anchor="w", text_color=txt_color, command=lambda: self.select_frame_by_name("auto"))
        self.btn_auto.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_extract = ctk.CTkButton(self.sidebar_frame, text=self.get_text("tab_extract"), anchor="w", text_color=txt_color, command=lambda: self.select_frame_by_name("extract"))
        self.btn_extract.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_compress = ctk.CTkButton(self.sidebar_frame, text=self.get_text("tab_compress"), anchor="w", text_color=txt_color, command=lambda: self.select_frame_by_name("compress"))
        self.btn_compress.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text=self.get_text("tab_settings"), anchor="w", text_color=txt_color, command=lambda: self.select_frame_by_name("settings"))
        self.btn_settings.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_about = ctk.CTkButton(self.sidebar_frame, text=self.get_text("tab_about"), anchor="w", text_color=txt_color, command=lambda: self.select_frame_by_name("about"))
        self.btn_about.grid(row=7, column=0, padx=20, pady=(10, 30), sticky="ew")

    def _build_main_area(self):
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content.grid_rowconfigure(0, weight=3) 
        self.main_content.grid_rowconfigure(1, weight=1) 
        self.main_content.grid_columnconfigure(0, weight=1)
        
        self.view_container = ctk.CTkFrame(self.main_content, corner_radius=10)
        self.view_container.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        
        self.console_frame = ctk.CTkFrame(self.main_content, corner_radius=10)
        self.console_frame.grid(row=1, column=0, sticky="nsew")
        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)
        
        self.console_textbox = ctk.CTkTextbox(self.console_frame, font=ctk.CTkFont(family="Monospace", size=13))
        self.console_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.log_message(self.get_text("log_ready"))

    def log_message(self, message: str):
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", message + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def _build_frames(self):
        self.frames = {}
        for name in ["auto", "extract", "compress", "settings", "about"]:
            frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

        self._build_action_tab(self.frames["auto"], "tab_auto", "Full Pipeline: Extracts the ISO (XDVDFS) and compresses to ZArchive sequentially.", "auto")
        self._build_action_tab(self.frames["extract"], "tab_extract", "Isolated Tool: Only extracts the file structure from the ISO (XDVDFS).", "extract")
        self._build_action_tab(self.frames["compress"], "tab_compress", "Isolated Tool: Only compresses a structured folder into .zar format.", "compress")

        self._populate_settings_frame(self.frames["settings"])
        self._populate_about_frame(self.frames["about"])

    def _build_action_tab(self, frame, title_key: str, description: str, mode: str):
        frame.grid_rowconfigure(2, weight=1) 
        frame.grid_columnconfigure(0, weight=1)
        
        lbl_title = ctk.CTkLabel(frame, text=self.get_text(title_key), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.grid(row=0, column=0, sticky="w", padx=30, pady=(30, 5))
        
        lbl_desc = ctk.CTkLabel(frame, text=description, text_color="gray", font=ctk.CTkFont(size=12))
        lbl_desc.grid(row=1, column=0, sticky="w", padx=30, pady=(0, 15))

        sel_frame = ctk.CTkFrame(frame, fg_color="transparent")
        sel_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=5)
        sel_frame.grid_rowconfigure(1, weight=1)
        sel_frame.grid_columnconfigure(0, weight=1)
        sel_frame.grid_columnconfigure(1, weight=1)

        dir_frame = ctk.CTkFrame(sel_frame, fg_color="transparent")
        dir_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(dir_frame, text=self.get_text("lbl_source"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        src_frame = ctk.CTkFrame(dir_frame, fg_color="transparent")
        src_frame.pack(fill="x", pady=(0, 15))
        entry_src = ctk.CTkEntry(src_frame)
        entry_src.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_src.insert(0, self.cfg.get("source_dir"))
        btn_src = ctk.CTkButton(src_frame, text="Browse...", width=100, fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white", command=lambda: self.select_folder("source_dir", entry_src, mode))
        btn_src.pack(side="right")

        ctk.CTkLabel(dir_frame, text=self.get_text("lbl_target"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        tgt_frame = ctk.CTkFrame(dir_frame, fg_color="transparent")
        tgt_frame.pack(fill="x")
        entry_tgt = ctk.CTkEntry(tgt_frame)
        entry_tgt.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_tgt.insert(0, self.cfg.get("target_dir"))
        btn_tgt = ctk.CTkButton(tgt_frame, text="Browse...", width=100, fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white", command=lambda: self.select_folder("target_dir", entry_tgt))
        btn_tgt.pack(side="right")

        ctk.CTkLabel(sel_frame, text="Itens Identificados (Selecione para processar):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="sw", padx=(10, 0), pady=(0, 5))
        btn_toggle = ctk.CTkButton(sel_frame, text="Marcar/Desmarcar Todos", width=180, fg_color="gray", hover_color="darkgray", command=lambda m=mode: self.toggle_all_selections(m))
        btn_toggle.grid(row=0, column=1, sticky="se", padx=(10, 0), pady=(0, 5))
        
        self.tab_data[mode]["scroll_frame"] = ctk.CTkScrollableFrame(sel_frame, height=120)
        self.tab_data[mode]["scroll_frame"].grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))

        bot_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bot_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=15)
        bot_frame.grid_columnconfigure(0, weight=1)

        self.tab_data[mode]["tasks_frame"] = ctk.CTkFrame(bot_frame, fg_color=("gray85", "gray15"), corner_radius=5)
        self.tab_data[mode]["tasks_frame"].grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Sub-frame para alinhar o contador e a porcentagem perfeitamente
        info_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        info_frame.grid_columnconfigure(0, weight=1)
        
        lbl_counter = ctk.CTkLabel(info_frame, text="0 / 0 itens concluídos", font=ctk.CTkFont(weight="bold"))
        lbl_counter.pack(side="left")
        self.tab_data[mode]["lbl_counter"] = lbl_counter

        lbl_percentage = ctk.CTkLabel(info_frame, text="0%", font=ctk.CTkFont(weight="bold"))
        lbl_percentage.pack(side="right")
        self.tab_data[mode]["lbl_percentage"] = lbl_percentage

        prog_bar = ctk.CTkProgressBar(bot_frame, progress_color=self.theme_data["accent"])
        prog_bar.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        prog_bar.set(0)
        self.tab_data[mode]["progress"] = prog_bar

        ctrl_frame = ctk.CTkFrame(bot_frame, fg_color="transparent")
        ctrl_frame.grid(row=2, column=1, sticky="e", padx=(15, 0))
        
        btn_start = ctk.CTkButton(ctrl_frame, text="Iniciar Lote", height=35, font=ctk.CTkFont(weight="bold"), fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white", command=lambda m=mode: self.start_process(m))
        btn_start.pack(side="left", padx=(0, 10))
        
        btn_pause = ctk.CTkButton(ctrl_frame, text="Pausar Fila", height=35, font=ctk.CTkFont(weight="bold"), fg_color="gray", hover_color="darkgray", state="disabled", command=lambda m=mode: self.toggle_pause_process(m))
        btn_pause.pack(side="left", padx=(0, 10))
        
        btn_cancel = ctk.CTkButton(ctrl_frame, text="Cancelar Operação", height=35, font=ctk.CTkFont(weight="bold"), fg_color="#8B0000", hover_color="#660000", text_color="white", state="disabled", command=lambda m=mode: self.cancel_process(m))
        btn_cancel.pack(side="left")

        self.tab_data[mode]["btns"]["start"] = btn_start
        self.tab_data[mode]["btns"]["pause"] = btn_pause
        self.tab_data[mode]["btns"]["cancel"] = btn_cancel

    def _populate_settings_frame(self, frame):
        lbl_title = ctk.CTkLabel(frame, text=self.get_text("tab_settings"), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(anchor="w", padx=30, pady=(30, 20))

        ctk.CTkLabel(frame, text=self.get_text("lbl_language")).pack(anchor="w", padx=30, pady=(10, 0))
        self.lang_var = ctk.StringVar(value=self.cfg.get("language"))
        combo_lang = ctk.CTkComboBox(frame, variable=self.lang_var, values=["pt-br", "en"], width=200, button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"], command=self.on_setting_change)
        combo_lang.pack(anchor="w", padx=30, pady=(5, 20))

        ctk.CTkLabel(frame, text=self.get_text("lbl_theme")).pack(anchor="w", padx=30, pady=(10, 0))
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme"))
        combo_theme = ctk.CTkComboBox(frame, variable=self.theme_var, values=["Sistema", "Preto", "Branco", "Steam", "Xbox"], width=200, button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"], command=self.on_setting_change)
        combo_theme.pack(anchor="w", padx=30, pady=(5, 20))

        ctk.CTkLabel(frame, text=f'{self.get_text("lbl_workers")} (Atual: {self.cfg.get("workers")})').pack(anchor="w", padx=30, pady=(10, 0))
        slider_workers = ctk.CTkSlider(frame, from_=1, to=16, number_of_steps=15, width=400, button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"], progress_color=self.theme_data["accent"], command=self.on_worker_slider_change)
        slider_workers.set(self.cfg.get("workers"))
        slider_workers.pack(anchor="w", padx=30, pady=(5, 5))
        
        ctk.CTkLabel(frame, text="Aviso de Performance: Alocar uma quantidade excessiva de threads pode causar sobrecarga severa no disco (I/O Bottleneck), \nresultando em perda dramática de velocidade. O ideal é manter um valor moderado (2 a 4) para discos rígidos.", text_color="orange", justify="left").pack(anchor="w", padx=30, pady=(0, 20))

    def _populate_about_frame(self, frame):
        lbl_title = ctk.CTkLabel(frame, text=self.get_text("about_title"), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(anchor="w", padx=30, pady=(30, 10))
        lbl_desc = ctk.CTkLabel(frame, text=self.get_text("about_desc"), wraplength=700, justify="left")
        lbl_desc.pack(anchor="w", padx=30, pady=(0, 20))
        tutorial_frame = ctk.CTkFrame(frame, fg_color=("gray85", "gray15"), corner_radius=10)
        tutorial_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(tutorial_frame, text=self.get_text("about_tutorial"), wraplength=650, justify="left").pack(padx=20, pady=20, anchor="w")
        btn_github = ctk.CTkButton(frame, text=self.get_text("btn_github"), fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white", command=lambda: webbrowser.open("https://github.com/SeuUsuario/ZarManager"))
        btn_github.pack(anchor="w", padx=30, pady=20)
        ctk.CTkLabel(frame, text=self.get_text("lbl_update"), font=ctk.CTkFont(weight="bold", slant="italic")).pack(anchor="w", padx=30, pady=10)

    def select_frame_by_name(self, name: str):
        self.current_frame_name = name
        base_text_color = self.theme_data["text"]
        for btn in [self.btn_auto, self.btn_extract, self.btn_compress, self.btn_settings, self.btn_about]:
            btn.configure(fg_color="transparent", text_color=base_text_color)
            
        accent = self.theme_data["accent"]
        active_text_color = "white"
        
        if name == "auto": self.btn_auto.configure(fg_color=accent, text_color=active_text_color)
        elif name == "extract": self.btn_extract.configure(fg_color=accent, text_color=active_text_color)
        elif name == "compress": self.btn_compress.configure(fg_color=accent, text_color=active_text_color)
        elif name == "settings": self.btn_settings.configure(fg_color=accent, text_color=active_text_color)
        elif name == "about": self.btn_about.configure(fg_color=accent, text_color=active_text_color)

        for frame_name, frame in self.frames.items():
            if frame_name == name:
                frame.tkraise()
                
    def on_setting_change(self, choice):
        self.cfg.set("language", self.lang_var.get())
        self.cfg.set("theme", self.theme_var.get())
        self.log_message(f"[SISTEMA] Refatorando interface gráfica para: {self.theme_var.get()} / {self.lang_var.get()}...")
        self.refresh_ui()

    def on_worker_slider_change(self, value):
        self.cfg.set("workers", int(value))

if __name__ == "__main__":
    app = ZarManagerGUI()
    app.mainloop()