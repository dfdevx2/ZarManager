# locales.py

TRANSLATIONS = {
    "pt-br": {
        "app_title": "ZarManager",
        "tab_auto": "Modo Automatizado",
        "tab_extract": "Apenas Extrair",
        "tab_compress": "Apenas Comprimir",
        "tab_settings": "Configurações",
        "tab_about": "Sobre",
        "lbl_source": "Diretório de Origem:",
        "lbl_target": "Diretório de Destino:",
        "lbl_language": "Idioma da Interface:",
        "lbl_theme": "Tema Visual:",
        "lbl_workers": "Threads de Processamento",
        "log_ready": "Sistema pronto para operação.",
        "about_title": "Sobre o ZarManager",
        "about_desc": "Uma ferramenta gráfica multiplataforma para extração e compressão de arquivos XISO.",
        "about_tutorial": "Instruções:\n1. Selecione o modo de operação na lateral.\n2. Defina os diretórios de origem e destino.\n3. Selecione os arquivos e inicie o lote.",
        "btn_github": "Acessar Código Fonte",
        "lbl_update": "Atualizações disponíveis via GitHub Releases.",
        
        # Dicas flutuantes (Tooltips)
        "tip_auto": "Ciclo completo: Extrai a ISO original e compacta imediatamente para o formato .zar.",
        "tip_extract": "Ferramenta isolada: Apenas extrai os arquivos da ISO para uma pasta.",
        "tip_compress": "Ferramenta isolada: Apenas compacta uma pasta já extraída para o formato .zar.",
        "tip_source": "Selecione a pasta raiz onde os seus arquivos ou ISOs estão armazenados.",
        "tip_target": "Selecione o local exato onde os arquivos processados deverão ser salvos.",
        "tip_start": "Inicia o processamento massivo da fila selecionada.",
        "tip_pause": "Congela a fila. Tarefas ativas terminarão, mas novas não serão iniciadas.",
        "tip_cancel": "Aborta criticamente o processo e destrói os arquivos temporários criados."
    },
    "en": {
        "app_title": "ZarManager",
        "tab_auto": "Automated Pipeline",
        "tab_extract": "Extract Only",
        "tab_compress": "Compress Only",
        "tab_settings": "Settings",
        "tab_about": "About",
        "lbl_source": "Source Directory:",
        "lbl_target": "Target Directory:",
        "lbl_language": "Interface Language:",
        "lbl_theme": "Visual Theme:",
        "lbl_workers": "Processing Threads",
        "log_ready": "System ready for operation.",
        "about_title": "About ZarManager",
        "about_desc": "A cross-platform GUI tool for XISO extraction and compression.",
        "about_tutorial": "Instructions:\n1. Select the operation mode on the sidebar.\n2. Set the source and target directories.\n3. Select the files and start the batch.",
        "btn_github": "Access Source Code",
        "lbl_update": "Updates available via GitHub Releases.",
        
        # Floating tooltips
        "tip_auto": "Full cycle: Extracts the original ISO and immediately compresses it to .zar format.",
        "tip_extract": "Isolated tool: Only extracts files from the ISO into a folder.",
        "tip_compress": "Isolated tool: Only compresses an already extracted folder into .zar format.",
        "tip_source": "Select the root folder where your files or ISOs are stored.",
        "tip_target": "Select the exact location where the processed files should be saved.",
        "tip_start": "Starts mass processing of the selected queue.",
        "tip_pause": "Freezes the queue. Active tasks will finish, but no new ones will start.",
        "tip_cancel": "Critically aborts the process and destroys created temporary files."
    }
}

def get_text(lang: str, key: str) -> str:
    """Retorna o texto correspondente à chave no idioma especificado."""
    if lang not in TRANSLATIONS:
        lang = "pt-br"
    return TRANSLATIONS[lang].get(key, key)