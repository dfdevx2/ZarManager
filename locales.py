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
        "lbl_auto_update": "Verificar atualizações automaticamente ao abrir",
        "log_ready": "Sistema pronto para operação.",
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
        
        # Popups
        "msg_collision_title": "Conflito de Arquivos",
        "msg_collision_desc": "Alguns itens selecionados já existem no diretório de destino.\n\n• Sim: Sobrescrever todos os existentes.\n• Não: Pular os existentes e processar apenas os novos.\n• Cancelar: Abortar a operação.",
        "msg_queue_empty": "Todos os itens conflitantes foram pulados. A fila está vazia.",
        "msg_update_popup_title": "Nova Versão Disponível",
        "msg_update_popup_desc": "A versão {} do ZarManager foi lançada!\n\nDeseja abrir o navegador para baixar a atualização agora?",

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
        "lbl_auto_update": "Check for updates automatically on startup",
        "log_ready": "System ready for operation.",
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
        
        # Popups
        "msg_collision_title": "File Collision",
        "msg_collision_desc": "Some selected items already exist in the target directory.\n\n• Yes: Overwrite all existing files.\n• No: Skip existing files and process only new ones.\n• Cancel: Abort the operation.",
        "msg_queue_empty": "All conflicting items were skipped. The queue is empty.",
        "msg_update_popup_title": "New Version Available",
        "msg_update_popup_desc": "Version {} of ZarManager has been released!\n\nDo you want to open the browser to download it now?",

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
    if lang not in TRANSLATIONS:
        lang = "pt-br"
    return TRANSLATIONS[lang].get(key, key)