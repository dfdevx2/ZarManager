TRANSLATIONS = {
    "pt-br": {
        # === TÍTULOS E ABAS ===
        "app_title": "ZarManager",
        "tab_auto": "Modo Automatizado (Universal)",
        "tab_extract_arc": "Extrair Arquivos (7z)",
        "tab_extract": "Apenas Extrair ISO",
        "tab_compress": "Apenas Comprimir",
        "tab_settings": "Configurações",
        "tab_about": "Sobre",
        
        # === TELA DE BOAS-VINDAS ===
        "msg_welcome": "Bem-vindo",
        "msg_choose_theme": "Escolha o tema visual inicial:",
        "btn_continue": "Continuar",
        
        # === INTERFACE PRINCIPAL ===
        "lbl_directories": "Diretórios",
        "lbl_source": "Diretório de Origem:",
        "lbl_target": "Diretório de Destino:",
        "lbl_search_source": "Procurar Origem...",
        "lbl_search_target": "Procurar Destino...",
        "lbl_selectable_items": "Itens Selecionáveis:",
        "btn_invert_sel": "Inverter Seleção",
        "msg_no_files": "Nenhum ficheiro compatível encontrado na pasta.",
        "lbl_console": "Console de Registo",
        
        # === BOTÕES DE CONTROLO ===
        "btn_start_proc": "▶ Iniciar Processamento",
        "btn_pause_proc": "⏸ Pausar Fila",
        "btn_resume_proc": "▶ Retomar Fila",
        "btn_cancel_proc": "⏹ Cancelar Operação",
        "lbl_processed": "processados",
        
        # === CONFIGURAÇÕES ===
        "lbl_language": "Idioma da Interface",
        "lbl_theme": "Tema Visual",
        "lbl_workers": "Threads de Processamento",
        "worker_warning": "Aviso de Performance: Alocar uma quantidade excessiva de threads pode causar sobrecarga severa no disco (I/O Bottleneck), resultando em perda dramática de velocidade. O ideal é manter um valor moderado (2 a 4) para discos rígidos.",
        
        # === SOBRE ===
        "about_title": "Sobre o ZarManager",
        "about_desc": "Uma ferramenta gráfica multiplataforma para extração e compressão de arquivos XISO.",
        "lbl_about_dev": "Desenvolvedor",
        "btn_repo": "🌐 Repositório Oficial no GitHub",
        "lbl_how_to_use": "Como Usar",
        "about_tutorial": "Instruções:\n1. Selecione o modo de operação na aba superior.\n2. Defina os diretórios de origem e destino.\n3. Selecione os arquivos e inicie o lote.",
        "lbl_auto_update": "Verificar atualizações automaticamente ao iniciar",
        "btn_check_update": "Verificar Atualizações",
        "btn_download_update": "Baixar Nova Versão",
        
        # === SISTEMA E ATUALIZAÇÕES ===
        "log_ready": "Sistema pronto para operação. Listagem otimizada nativa ativa.",
        "msg_checking_update": "Consultando os servidores do GitHub...",
        "msg_update_avail": "Nova versão ({}) disponível!",
        "msg_update_latest": "O sistema está atualizado (Versão {}).",
        "msg_update_error": "Falha na comunicação com o servidor.",
        "msg_update_popup_title": "Nova Versão Disponível",
        "msg_update_popup_desc": "A versão {} do ZarManager foi lançada!\n\nDeseja abrir o navegador para baixar a atualização agora?",
        
        # === DIÁLOGOS DE CONFLITO E EXCLUSÃO ===
        "msg_collision_title": "Conflito de Arquivos",
        "msg_collision_desc": "Alguns itens selecionados já existem no diretório de destino.\n\n• Sobrescrever: Substitui os ficheiros existentes.\n• Pular Existentes: Ignora e processa apenas os novos.\n• Cancelar: Abortar a operação.",
        "msg_queue_empty": "Todos os itens conflitantes foram pulados. A fila está vazia.",
        "btn_cancel": "Cancelar",
        "btn_skip_existing": "Pular Existentes",
        "btn_overwrite": "Sobrescrever",
        
        "delete_title": "Manter Arquivos Originais?",
        "delete_msg": "Por padrão, a ferramenta deleta os arquivos de origem (ISOs, ZIPs, Pastas) após o sucesso da operação para economizar espaço no disco.\n\nDeseja MANTER os arquivos originais?\n\n• Manter Originais: Mantém a origem e o arquivo gerado.\n• Apagar (Padrão): Exclui a origem após gerar o arquivo.",
        "btn_delete_default": "Apagar (Padrão)",
        "btn_keep_originals": "Manter Originais",

        # === DIÁLOGO DE ENCERRAMENTO (ANTI-GHOSTING) ===
        "warn_exit_title": "Aviso de Encerramento",
        "warn_exit_msg": "Existem processos ativos em segundo plano.\nSe fechar agora, o programa irá cancelar e abortar tudo de forma segura.\n\nDeseja mesmo sair?",
        "btn_exit_yes": "Sair e Abortar",
        "btn_exit_no": "Cancelar e Voltar",

        # === STATUS DO PROCESSAMENTO ===
        "log_extracting_iso": "EXTRAINDO ISO",
        "log_extracting_arc": "DESCOMPACTANDO",
        "log_compressing": "COMPRIMINDO ZAR",
        "log_completed": "CONCLUÍDO",
        "log_failed": "FALHA",
        "log_cancelled": "CANCELADO",

        # === DICAS / TOOLTIPS ===
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
        # === TITLES AND TABS ===
        "app_title": "ZarManager",
        "tab_auto": "Automated Pipeline (Universal)",
        "tab_extract_arc": "Extract Archives (7z)",
        "tab_extract": "Extract ISO Only",
        "tab_compress": "Compress Only",
        "tab_settings": "Settings",
        "tab_about": "About",
        
        # === WELCOME SCREEN ===
        "msg_welcome": "Welcome",
        "msg_choose_theme": "Choose your initial visual theme:",
        "btn_continue": "Continue",
        
        # === MAIN INTERFACE ===
        "lbl_directories": "Directories",
        "lbl_source": "Source Directory:",
        "lbl_target": "Target Directory:",
        "lbl_search_source": "Browse Source...",
        "lbl_search_target": "Browse Target...",
        "lbl_selectable_items": "Selectable Items:",
        "btn_invert_sel": "Invert Selection",
        "msg_no_files": "No compatible files found in this folder.",
        "lbl_console": "Log Console",
        
        # === CONTROL BUTTONS ===
        "btn_start_proc": "▶ Start Processing",
        "btn_pause_proc": "⏸ Pause Queue",
        "btn_resume_proc": "▶ Resume Queue",
        "btn_cancel_proc": "⏹ Cancel Operation",
        "lbl_processed": "processed",
        
        # === SETTINGS ===
        "lbl_language": "Interface Language",
        "lbl_theme": "Visual Theme",
        "lbl_workers": "Processing Threads",
        "worker_warning": "Performance Warning: Allocating an excessive number of threads can cause severe disk overload (I/O Bottleneck), resulting in a dramatic loss of speed. It is ideal to keep a moderate value (2 to 4) for hard drives.",
        
        # === ABOUT ===
        "about_title": "About ZarManager",
        "about_desc": "A cross-platform GUI tool for XISO extraction and compression.",
        "lbl_about_dev": "Developer",
        "btn_repo": "🌐 Official GitHub Repository",
        "lbl_how_to_use": "How to Use",
        "about_tutorial": "Instructions:\n1. Select the operation mode on the top tab.\n2. Set the source and target directories.\n3. Select the files and start the batch processing.",
        "lbl_auto_update": "Check for updates automatically on startup",
        "btn_check_update": "Check for Updates",
        "btn_download_update": "Download New Version",
        
        # === SYSTEM AND UPDATES ===
        "log_ready": "System ready for operation. Optimized native listing active.",
        "msg_checking_update": "Querying GitHub servers...",
        "msg_update_avail": "New version ({}) available!",
        "msg_update_latest": "System is up to date (Version {}).",
        "msg_update_error": "Failed to communicate with the server.",
        "msg_update_popup_title": "New Version Available",
        "msg_update_popup_desc": "Version {} of ZarManager has been released!\n\nDo you want to open your browser to download the update now?",
        
        # === COLLISION AND DELETION DIALOGS ===
        "msg_collision_title": "File Collision",
        "msg_collision_desc": "Some selected items already exist in the target directory.\n\n• Overwrite: Replaces existing files.\n• Skip Existing: Ignores duplicates and processes only new ones.\n• Cancel: Abort the operation.",
        "msg_queue_empty": "All conflicting items were skipped. The queue is empty.",
        "btn_cancel": "Cancel",
        "btn_skip_existing": "Skip Existing",
        "btn_overwrite": "Overwrite",
        
        "delete_title": "Keep Original Files?",
        "delete_msg": "By default, the tool deletes source files (ISOs, ZIPs, Folders) after a successful operation to save disk space.\n\nDo you want to KEEP the original files?\n\n• Keep Originals: Keeps both the source and the generated file.\n• Delete (Default): Deletes the source after generation.",
        "btn_delete_default": "Delete (Default)",
        "btn_keep_originals": "Keep Originals",

        # === EXIT DIALOG (ANTI-GHOSTING) ===
        "warn_exit_title": "Exit Warning",
        "warn_exit_msg": "There are active background processes running.\nIf you exit now, the program will safely cancel and abort everything.\n\nDo you really want to exit?",
        "btn_exit_yes": "Exit and Abort",
        "btn_exit_no": "Cancel and Return",

        # === STATUS DO PROCESSAMENTO ===
        "log_extracting_iso": "EXTRACTING ISO",
        "log_extracting_arc": "EXTRACTING ARCHIVE",
        "log_compressing": "COMPRESSING ZAR",
        "log_completed": "COMPLETED",
        "log_failed": "FAILED",
        "log_cancelled": "CANCELLED",

        # === TIPS / TOOLTIPS ===
        "tip_auto": "Smart Cycle: Reads ZIPs, ISOs, or Folders. Runs full pipeline to .zar.",
        "tip_extract_arc": "Isolated: Extracts archives flatly (no nested folders).",
        "tip_extract": "Isolated: Extracts ISO files (XDVDFS) to a folder.",
        "tip_compress": "Isolated: Compresses an extracted folder to .zar format.",
        "tip_source": "Select the folder where the original files are located.",
        "tip_target": "Select the folder where the finished files should be saved.",
        "tip_start": "Starts mass processing.",
        "tip_pause": "Freezes the queue.",
        "tip_cancel": "Cancels and cleans up ongoing operations."
    }
}

def get_text(lang: str, key: str) -> str:
    if lang not in TRANSLATIONS:
        lang = "pt-br"
    return TRANSLATIONS[lang].get(key, key)