# app.py
# Interface Gráfica Dinâmica (GUI) - Ferramentas de Processamento e Multithreading

import customtkinter as ctk
import webbrowser
import threading
from tkinter import filedialog
from config import ConfigManager
import locales
from core import ZarManagerCore

# Mapeamento Hexadecimal Absoluto das Marcas e Modos
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
        self.geometry("1050x700")
        self.minsize(900, 600)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.current_frame_name = "auto"
        self.build_all()

    def get_text(self, key: str) -> str:
        return locales.get_text(self.cfg.get("language"), key)

    def apply_appearance(self):
        theme_name = self.cfg.get("theme")
        if theme_name not in THEME_COLORS:
            theme_name = "Sistema"
            
        self.theme_data = THEME_COLORS[theme_name]
        ctk.set_appearance_mode(self.theme_data["mode"])

    def build_all(self):
        self.apply_appearance()
        self.title(self.get_text("app_title"))
        
        self._build_sidebar()
        self._build_main_area()
        self._build_frames()
        
        self.select_frame_by_name(self.current_frame_name)

    def refresh_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.build_all()

    # -------------------------------------------------------------------------
    # INTERAÇÕES DO SISTEMA E PROCESSAMENTO (MULTITHREADING)
    # -------------------------------------------------------------------------
    def select_folder(self, config_key: str, entry_widget: ctk.CTkEntry):
        """Abre o seletor nativo do sistema e salva a escolha no config.json."""
        current_path = self.cfg.get(config_key)
        selected_dir = filedialog.askdirectory(initialdir=current_path if current_path else "/")
        
        if selected_dir:
            self.cfg.set(config_key, selected_dir)
            entry_widget.delete(0, "end")
            entry_widget.insert(0, selected_dir)
            self.log_message(f"[SISTEMA] {config_key} atualizado para: {selected_dir}")

    def start_process(self, mode: str):
        """Inicia a thread secundária para evitar o congelamento da interface."""
        source = self.cfg.get("source_dir")
        target = self.cfg.get("target_dir")
        workers = self.cfg.get("workers")
        
        if not source or not target:
            self.log_message("[ERRO] Diretório de origem ou destino não selecionado.")
            return

        # Zera a barra de progresso antes de iniciar
        self.progress.set(0)
        self.log_message(f"[SISTEMA] Instanciando motor de processamento no modo: {mode.upper()}...")
        
        # Cria a thread isolada apontando para a execução do core
        process_thread = threading.Thread(target=self._run_core_logic, args=(source, target, workers, mode), daemon=True)
        process_thread.start()

    def _run_core_logic(self, source, target, workers, mode):
        """Método executado fora da MainThread da interface."""
        manager = ZarManagerCore(
            source_directory=source,
            target_directory=target,
            max_workers=workers,
            mode=mode,
            log_callback=self._update_log_from_thread,
            progress_callback=self._update_progress_from_thread
        )
        
        if manager.verify_environment():
            manager.scan_files()
            manager.start_processing()
        else:
            self._update_log_from_thread("[ERRO CRÍTICO] Execução abortada por falha no ambiente.")

    def _update_log_from_thread(self, message: str):
        """Injeta os logs do core na interface de forma segura via after()."""
        self.after(0, lambda: self.log_message(message))

    def _update_progress_from_thread(self, current: int, total: int):
        """Calcula e atualiza a barra de progresso de forma segura."""
        if total > 0:
            percentage = current / total
            self.after(0, lambda: self.progress.set(percentage))

    # -------------------------------------------------------------------------
    # CONSTRUÇÃO DO MENU LATERAL
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # CONSTRUÇÃO DA ÁREA CENTRAL
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # CONTEÚDO DAS ABAS E ROTEAMENTO
    # -------------------------------------------------------------------------
    def _build_frames(self):
        self.frames = {}
        for name in ["auto", "extract", "compress", "settings", "about"]:
            frame = ctk.CTkFrame(self.view_container, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

        self._build_action_tab(self.frames["auto"], "tab_auto", "Fluxo Completo: Extrai a ISO (XDVDFS) e compacta para ZArchive em sequência.", "auto")
        self._build_action_tab(self.frames["extract"], "tab_extract", "Ferramenta Isolada: Apenas extrai a estrutura de arquivos da ISO (XDVDFS).", "extract")
        self._build_action_tab(self.frames["compress"], "tab_compress", "Ferramenta Isolada: Apenas compacta uma pasta estruturada para o formato .zar.", "compress")

        self._populate_settings_frame(self.frames["settings"])
        self._populate_about_frame(self.frames["about"])

    def _build_action_tab(self, frame, title_key: str, description: str, mode: str):
        lbl_title = ctk.CTkLabel(frame, text=self.get_text(title_key), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(anchor="w", padx=30, pady=(30, 5))
        
        lbl_desc = ctk.CTkLabel(frame, text=description, text_color="gray", font=ctk.CTkFont(size=12))
        lbl_desc.pack(anchor="w", padx=30, pady=(0, 20))

        # Origem
        ctk.CTkLabel(frame, text=self.get_text("lbl_source"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=30, pady=(10, 0))
        src_frame = ctk.CTkFrame(frame, fg_color="transparent")
        src_frame.pack(fill="x", padx=30, pady=(5, 15))
        
        entry_src = ctk.CTkEntry(src_frame)
        entry_src.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_src.insert(0, self.cfg.get("source_dir"))
        
        btn_src = ctk.CTkButton(src_frame, text=self.get_text("btn_browse"), width=120, 
                                fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white",
                                command=lambda: self.select_folder("source_dir", entry_src))
        btn_src.pack(side="right")

        # Destino
        ctk.CTkLabel(frame, text=self.get_text("lbl_target"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=30, pady=(10, 0))
        tgt_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tgt_frame.pack(fill="x", padx=30, pady=(5, 25))
        
        entry_tgt = ctk.CTkEntry(tgt_frame)
        entry_tgt.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_tgt.insert(0, self.cfg.get("target_dir"))
        
        btn_tgt = ctk.CTkButton(tgt_frame, text=self.get_text("btn_browse"), width=120, 
                                fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white",
                                command=lambda: self.select_folder("target_dir", entry_tgt))
        btn_tgt.pack(side="right")

        # Progresso e Botão Start (Agora apontando para start_process)
        prog_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prog_frame.pack(fill="x", padx=30, pady=20, side="bottom")

        btn_start = ctk.CTkButton(prog_frame, text=self.get_text("btn_start"), height=40, font=ctk.CTkFont(weight="bold"),
                                  fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white",
                                  command=lambda m=mode: self.start_process(m))
        btn_start.pack(side="right", padx=(10, 0))

        self.progress = ctk.CTkProgressBar(prog_frame, progress_color=self.theme_data["accent"])
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(0)

    def _populate_settings_frame(self, frame):
        lbl_title = ctk.CTkLabel(frame, text=self.get_text("tab_settings"), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(anchor="w", padx=30, pady=(30, 20))

        ctk.CTkLabel(frame, text=self.get_text("lbl_language")).pack(anchor="w", padx=30, pady=(10, 0))
        self.lang_var = ctk.StringVar(value=self.cfg.get("language"))
        combo_lang = ctk.CTkComboBox(frame, variable=self.lang_var, values=["pt-br", "en"], width=200, 
                                     button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"],
                                     command=self.on_setting_change)
        combo_lang.pack(anchor="w", padx=30, pady=(5, 20))

        ctk.CTkLabel(frame, text=self.get_text("lbl_theme")).pack(anchor="w", padx=30, pady=(10, 0))
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme"))
        combo_theme = ctk.CTkComboBox(frame, variable=self.theme_var, values=["Sistema", "Preto", "Branco", "Steam", "Xbox"], width=200,
                                      button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"],
                                      command=self.on_setting_change)
        combo_theme.pack(anchor="w", padx=30, pady=(5, 20))

        ctk.CTkLabel(frame, text=f'{self.get_text("lbl_workers")} (Atual: {self.cfg.get("workers")})').pack(anchor="w", padx=30, pady=(10, 0))
        slider_workers = ctk.CTkSlider(frame, from_=1, to=16, number_of_steps=15, width=400,
                                       button_color=self.theme_data["accent"], button_hover_color=self.theme_data["hover"],
                                       progress_color=self.theme_data["accent"],
                                       command=self.on_worker_slider_change)
        slider_workers.set(self.cfg.get("workers"))
        slider_workers.pack(anchor="w", padx=30, pady=(5, 20))

    def _populate_about_frame(self, frame):
        lbl_title = ctk.CTkLabel(frame, text=self.get_text("about_title"), font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(anchor="w", padx=30, pady=(30, 10))
        
        lbl_desc = ctk.CTkLabel(frame, text=self.get_text("about_desc"), wraplength=700, justify="left")
        lbl_desc.pack(anchor="w", padx=30, pady=(0, 20))
        
        tutorial_frame = ctk.CTkFrame(frame, fg_color=("gray85", "gray15"), corner_radius=10)
        tutorial_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(tutorial_frame, text=self.get_text("about_tutorial"), wraplength=650, justify="left").pack(padx=20, pady=20, anchor="w")
        
        btn_github = ctk.CTkButton(frame, text=self.get_text("btn_github"), 
                                   fg_color=self.theme_data["accent"], hover_color=self.theme_data["hover"], text_color="white",
                                   command=lambda: webbrowser.open("https://github.com/SeuUsuario/ZarManager"))
        btn_github.pack(anchor="w", padx=30, pady=20)
        
        ctk.CTkLabel(frame, text=self.get_text("lbl_update"), font=ctk.CTkFont(weight="bold", slant="italic")).pack(anchor="w", padx=30, pady=10)

    # -------------------------------------------------------------------------
    # ROTEAMENTO DE BOTÕES
    # -------------------------------------------------------------------------
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