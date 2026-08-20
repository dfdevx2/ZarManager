# locales.py

TRANSLATIONS = {
    "pt-br": {
        "app_title": "ZarManager",
        "tab_auto": "Modo Automatizado (Universal)",
        "tab_extract_arc": "Extrair Arquivos (7z)",
        "tab_extract": "Apenas Extrair ISO",
        "tab_compress": "Apenas Comprimir",
        "tab_settings": "Configurações",
        "tab_about": "Sobre",
        "lbl_source": "Diretório de Origem:",
        "lbl_target": "Diretório de Destino:",
        "lbl_language": "Idioma da Interface:",
        "lbl_theme": "Tema Visual:",
        "lbl_workers": "Threads de Processamento",
        "lbl_auto_update": "Verificar atualizações automaticamente ao iniciar",
        "log_ready": "Sistema pronto para operação. Listagem otimizada nativa ativa.",
        "about_title": "Sobre o ZarManager",
        "about_desc": "Uma ferramenta gráfica multiplataforma para extração e compressão de arquivos XISO.",
        "about_tutorial": "Instruções:\n1. Selecione o modo de operação na lateral.\n2. Defina os diretórios de origem e destino.\n3. Selecione os arquivos e inicie o lote.",
        "btn_github": "Acessar Código Fonte",
        "btn_check_update": "Verificar Atualizações",
        "btn_download_update": "Baixar Nova Versão",
        "msg_checking_update": "Consultando os servidores do GitHub...",
        "msg_update_avail": "Nova versão ({}) disponível!",
        "msg_update_latest": "O sistema está atualizado (Versão {}).",
        "msg_update_error": "Falha na comunicação com o servidor.",
        
        "msg_collision_title": "Conflito de Arquivos",
        "msg_collision_desc": "Alguns itens selecionados já existem no diretório de destino.\n\n• Sim: Sobrescrever todos.\n• Não: Pular existentes e processar novos.\n• Cancelar: Abortar a operação.",
        "msg_queue_empty": "Todos os itens conflitantes foram pulados. A fila está vazia.",
        "msg_update_popup_title": "Nova Versão Disponível",
        "msg_update_popup_desc": "A versão {} do ZarManager foi lançada!\n\nDeseja abrir o navegador para baixar a atualização agora?",

        "tip_auto": "Ciclo Inteligente: Lê ZIPs, ISOs ou Pastas. Faz a esteira completa até o final (.zar) e limpa os resíduos.",
        "tip_extract_arc": "Isolado: Extrai .zip, .rar ou .7z de forma plana (sem pastas aninhadas).",
        "tip_extract": "Isolado: Extrai os arquivos da ISO (XDVDFS) para uma pasta.",
        "tip_compress": "Isolado: Compacta uma pasta extraída para o formato .zar.",
        "tip_source": "Selecione a pasta onde os arquivos originais estão.",
        "tip_target": "Selecione a pasta onde os finalizados devem ser salvos.",
        "tip_start": "Inicia o processamento massivo.",
        "tip_pause": "Congela a fila.",
        "tip_cancel": "Cancela e limpa operações em andamento."
    },
    "en": {
        "app_title": "ZarManager",
        "tab_auto": "Automated Pipeline (Universal)",
        "tab_extract_arc": "Extract Archives (7z)",
        "tab_extract": "Extract ISO Only",
        "tab_compress": "Compress Only",
        "tab_settings": "Settings",
        "tab_about": "About",
        "lbl_source": "Source Directory:",
        "lbl_target": "Target Directory:",
        "lbl_language": "Interface Language:",
        "lbl_theme": "Visual Theme:",
        "lbl_workers": "Processing Threads",
        "lbl_auto_update": "Check for updates automatically on startup",
        "log_ready": "System ready for operation. Optimized native listing active.",
        "about_title": "About ZarManager",
        "about_desc": "A cross-platform GUI tool for XISO extraction and compression.",
        "about_tutorial": "Instructions:\n1. Select the operation mode on the sidebar.\n2. Set the source and target directories.\n3. Select the files and start the batch.",
        "btn_github": "Access Source Code",
        "btn_check_update": "Check for Updates",
        "btn_download_update": "Download New Version",
        "msg_checking_update": "Querying GitHub servers...",
        "msg_update_avail": "New version ({}) available!",
        "msg_update_latest": "System is up to date (Version {}).",
        "msg_update_error": "Failed to communicate with the server.",
        
        "msg_collision_title": "File Collision",
        "msg_collision_desc": "Some items already exist.\n\n• Yes: Overwrite.\n• No: Skip existing.\n• Cancel: Abort.",
        "msg_queue_empty": "All conflicting items were skipped. Queue empty.",
        "msg_update_popup_title": "New Version Available",
        "msg_update_popup_desc": "Version {} released!\n\nOpen browser to download?",

        "tip_auto": "Smart Cycle: Reads ZIPs, ISOs, or Folders. Runs full pipeline to .zar.",
        "tip_extract_arc": "Isolated: Extracts archives flatly (no nested folders).",
        "tip_extract": "Isolated: Extracts ISO to folder.",
        "tip_compress": "Isolated: Compresses folder to .zar.",
        "tip_source": "Select source folder.",
        "tip_target": "Select target folder.",
        "tip_start": "Starts processing.",
        "tip_pause": "Freezes queue.",
        "tip_cancel": "Cancels operations."
    }
}

def get_text(lang: str, key: str) -> str:
    if lang not in TRANSLATIONS:
        lang = "pt-br"
    return TRANSLATIONS[lang].get(key, key)