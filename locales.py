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
        
        # === TELA DE BOAS-VINDAS & TUTORIAL ===
        "msg_welcome": "Bem-vindo",
        "msg_choose_theme": "Escolha o tema visual inicial:",
        "btn_continue": "Continuar",
        "tut_title": "Guia Rápido & Avisos de Segurança 🚀",
        "tut_msg": "Bem-vindo ao ZarManager!\n\nPara começar, escolha o modo de operação nas abas superiores.\n1. Selecione a sua pasta de Origem (onde estão os seus ficheiros) e a de Destino.\n2. Marque os itens na lista que deseja processar.\n3. Pressione 'Iniciar Processamento'!\n\n🛡️ AVISO IMPORTANTE (WINDOWS):\nComo a ferramenta é um executável único, ela extrai os motores de compressão para a pasta temporária do sistema durante o uso. Antivírus (como o Windows Defender) podem apagar estes ficheiros silenciosamente por falso positivo, causando um [ERRO CRÍTICO] de ficheiros ausentes ao iniciar o processamento.\nPara evitar isto, adicione o ficheiro '.exe' do ZarManager à lista de Exclusões do seu Antivírus.\n\n💡 DICA DE OURO: Se tiver dúvidas sobre o que um botão faz, deixe o rato parado sobre ele durante 2 segundos e uma bolha explicativa irá aparecer.",
        
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
        "theme_system": "Sistema",
        "theme_black": "Preto",
        "theme_white": "Branco",
        "lbl_workers": "Threads de Processamento",
        "worker_warning": "Aviso de Performance: Alocar uma quantidade excessiva de threads pode causar sobrecarga severa no disco (I/O Bottleneck), resultando em perda dramática de velocidade. O ideal é manter um valor moderado (2 a 4) para discos rígidos.",
        
        # === SOBRE & TROUBLESHOOTING ===
        "about_title": "Sobre o ZarManager",
        "about_desc": "Uma ferramenta gráfica multiplataforma para extração e compressão de arquivos XISO.",
        "lbl_about_dev": "Desenvolvedor",
        "btn_repo": "🌐 Repositório Oficial no GitHub",
        "btn_kofi": "☕ Apoiar o Projeto no Ko-fi",
        "btn_troubleshoot": "🛠️ Resolução de Erros Comuns",
        "lbl_how_to_use": "Como Usar",
        "about_tutorial": "Instruções:\n1. Selecione o modo de operação na aba superior.\n2. Defina os diretórios de origem e destino.\n3. Selecione os arquivos e inicie o lote.",
        "lbl_auto_update": "Verificar atualizações automaticamente ao iniciar",
        "btn_check_update": "Verificar Atualizações",
        "btn_download_update": "Baixar Nova Versão",
        
        "diag_troubleshoot_title": "🛠️ Erros Comuns e Soluções",
        "diag_troubleshoot_msg": "Aqui estão as soluções rápidas para os problemas mais comuns por sistema operativo:\n\n🪟 WINDOWS\nErro: O processamento falha imediatamente ([CRITICAL ERROR] Motores ausentes).\nCausa: O Windows Defender ou Antivírus apagou os motores da pasta temporária por falso positivo.\nSolução: Adicione o executável do ZarManager à lista de Exclusões do seu Antivírus.\n\n🍏 MACOS\nErro: 'A aplicação está danificada e não pode ser aberta'.\nCausa: O Gatekeeper da Apple bloqueou o ficheiro (Quarentena).\nSolução: Abra o 'Terminal' do Mac e digite o seguinte comando (ajuste o caminho se necessário): xattr -cr /Applications/ZarManager.app\n\n🐧 LINUX\nErro: A AppImage não abre de todo ou não processa nada.\nCausa: Faltam permissões de execução ou a biblioteca FUSE.\nSolução: Clique com o botão direito na AppImage -> Propriedades -> Ative 'Permitir execução do ficheiro como programa'. Certifique-se também de que tem o pacote 'libfuse2' instalado no seu sistema.",
        
        # === SISTEMA E ATUALIZAÇÕES ===
        "log_ready": "Sistema pronto para operação. Listagem otimizada nativa ativa.",
        "log_lang_changed": "Idioma da interface alterado com sucesso.",
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

        # === VERIFICAÇÃO AMBIENTAL INTELIGENTE ===
        "log_env_ok": "[SISTEMA] Verificação concluída. Todos os motores embutidos estão operacionais e no local correto.",
        "err_title_win": "Erro Crítico: Ferramentas Bloqueadas (Antivírus)",
        "err_msg_win": "O ZarManager não conseguiu aceder aos seguintes motores embutidos:\n\n{0}\n\nNo Windows, isto ocorre quase sempre porque o Windows Defender (ou outro Antivírus) apagou os ficheiros silenciosamente da pasta temporária por 'falso positivo'.\n\nSOLUÇÃO:\n1. Adicione o ficheiro ZarManager.exe à lista de 'Exclusões' do seu Antivírus.\n2. Reinicie o ZarManager e tente novamente.",
        "err_title_mac": "Erro Crítico: Ficheiros Ausentes",
        "err_msg_mac": "O ZarManager não conseguiu aceder aos seguintes motores embutidos:\n\n{0}\n\nNo macOS, isto pode ocorrer se o pacote (.dmg) não foi montado corretamente ou se as permissões de extração foram bloqueadas.\n\nSOLUÇÃO:\n1. Certifique-se de ter arrastado o ZarManager para a pasta 'Aplicações' antes de abrir.\n2. Verifique se o sistema não bloqueou a execução nas 'Definições de Sistema > Privacidade e Segurança'.",
        "err_title_lin": "Erro Crítico: Permissões de Ficheiro",
        "err_msg_lin": "O ZarManager não conseguiu aceder aos seguintes motores embutidos:\n\n{0}\n\nNo Linux, isto geralmente é causado por falta de permissões na extração da AppImage ou falta do pacote FUSE.\n\nSOLUÇÃO:\n1. Clique com o botão direito no ficheiro .AppImage, vá a 'Propriedades' e ative 'Permitir execução do ficheiro como um programa'.\n2. Confirme que tem o pacote 'libfuse2' instalado no seu sistema.",

        # === STATUS DO PROCESSAMENTO ===
        "log_extracting_iso": "EXTRAINDO ISO",
        "log_extracting_arc": "DESCOMPACTANDO",
        "log_compressing": "COMPRIMINDO ZAR",
        "log_completed": "CONCLUÍDO",
        "log_failed": "FALHA",
        "log_cancelled": "CANCELADO",

        # === DICAS / TOOLTIPS ===
        "tip_auto": "Ciclo Inteligente: Lê ZIPs, ISOs ou Pastas. Faz a esteira completa até ao formato .zar e limpa resíduos.",
        "tip_extract_arc": "Modo Isolado: Extrai .zip, .rar ou .7z de forma limpa.",
        "tip_extract": "Modo Isolado: Extrai os arquivos internos da ISO (XDVDFS) para uma pasta.",
        "tip_compress": "Modo Isolado: Compacta uma pasta já extraída para o formato .zar.",
        "tip_source": "Clique para escolher a pasta onde estão os ficheiros que deseja processar.",
        "tip_target": "Clique para escolher a pasta onde os ficheiros prontos devem ser guardados.",
        "tip_invert": "Inverte a seleção atual dos itens na lista acima.",
        "tip_start": "Inicia o processamento da fila com base nos itens marcados.",
        "tip_pause": "Congela o processamento atual. Pode retomar a qualquer altura.",
        "tip_cancel": "Cancela a fila e limpa os ficheiros incompletos de forma segura.",
        "tip_theme": "Altera o esquema de cores. Pode exigir reiniciar o programa para aplicar paletas nativas.",
        "tip_lang": "Muda a linguagem da interface e dos logs em tempo real."
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
        
        # === WELCOME SCREEN & TUTORIAL ===
        "msg_welcome": "Welcome",
        "msg_choose_theme": "Choose your initial visual theme:",
        "btn_continue": "Continue",
        "tut_title": "Quick Start Guide & Warnings 🚀",
        "tut_msg": "Welcome to ZarManager!\n\nTo get started, pick an operation mode from the top tabs.\n1. Select your Source folder (where your files are) and your Target folder.\n2. Check the items you want to process in the list.\n3. Click 'Start Processing'!\n\n🛡️ IMPORTANT WARNING (WINDOWS):\nBecause the tool is a single-file executable, it extracts its background engines to your system's temp folder at runtime. Antivirus software (like Windows Defender) may falsely flag and silently delete these files, causing a [CRITICAL ERROR] for missing binaries.\nTo prevent this, please add the ZarManager '.exe' file to your Antivirus Exclusions list.\n\n💡 PRO TIP: If you're ever unsure about what a button does, leave your mouse over it for 2 seconds and a beautiful tooltip will appear.",
        
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
        "theme_system": "System",
        "theme_black": "Pitch Black",
        "theme_white": "White",
        "lbl_workers": "Processing Threads",
        "worker_warning": "Performance Warning: Allocating an excessive number of threads can cause severe disk overload (I/O Bottleneck), resulting in a dramatic loss of speed. It is ideal to keep a moderate value (2 to 4) for hard drives.",
        
        # === ABOUT & TROUBLESHOOTING ===
        "about_title": "About ZarManager",
        "about_desc": "A cross-platform GUI tool for XISO extraction and compression.",
        "lbl_about_dev": "Developer",
        "btn_repo": "🌐 Official GitHub Repository",
        "btn_kofi": "☕ Support the Project on Ko-fi",
        "btn_troubleshoot": "🛠️ Common Errors & Troubleshooting",
        "lbl_how_to_use": "How to Use",
        "about_tutorial": "Instructions:\n1. Select the operation mode on the top tab.\n2. Set the source and target directories.\n3. Select the files and start the batch processing.",
        "lbl_auto_update": "Check for updates automatically on startup",
        "btn_check_update": "Check for Updates",
        "btn_download_update": "Download New Version",
        
        "diag_troubleshoot_title": "🛠️ Troubleshooting & Fixes",
        "diag_troubleshoot_msg": "Here are the quick solutions for the most common issues across operating systems:\n\n🪟 WINDOWS\nError: Processing fails instantly ([CRITICAL ERROR] Missing Engines).\nCause: Windows Defender or Antivirus deleted the background engines from the temp folder as a false positive.\nSolution: Add the ZarManager executable to your Antivirus 'Exclusions' list.\n\n🍏 MACOS\nError: 'App is damaged and can't be opened'.\nCause: Apple's Gatekeeper blocked the file (Quarantine attribute).\nSolution: Open the Mac 'Terminal' and type the following command (adjust the path if needed): xattr -cr /Applications/ZarManager.app\n\n🐧 LINUX\nError: The AppImage won't open at all or doesn't process files.\nCause: Missing execution permissions or missing FUSE library.\nSolution: Right-click the AppImage -> Properties -> Enable 'Allow executing file as program'. Also, ensure you have the 'libfuse2' package installed on your system.",
        
        # === SYSTEM AND UPDATES ===
        "log_ready": "System ready for operation. Optimized native listing active.",
        "log_lang_changed": "Interface language changed successfully.",
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

        # === VERIFICAÇÃO AMBIENTAL INTELIGENTE ===
        "log_env_ok": "[SYSTEM] Verification complete. All embedded engines are in place and operational.",
        "err_title_win": "Critical Error: Tools Blocked (Antivirus)",
        "err_msg_win": "ZarManager could not access the following embedded engines:\n\n{0}\n\nOn Windows, this almost always happens because Windows Defender (or another Antivirus) silently deleted the files from the temp folder as a 'false positive'.\n\nSOLUTION:\n1. Add the ZarManager.exe file to your Antivirus 'Exclusions' list.\n2. Restart ZarManager and try again.",
        "err_title_mac": "Critical Error: Missing Files",
        "err_msg_mac": "ZarManager could not access the following embedded engines:\n\n{0}\n\nOn macOS, this can happen if the App Bundle was not mounted properly or extraction permissions were blocked.\n\nSOLUTION:\n1. Make sure you drag ZarManager to your 'Applications' folder before opening it.\n2. Check if your system blocked the execution under 'System Settings > Privacy & Security'.",
        "err_title_lin": "Critical Error: File Permissions",
        "err_msg_lin": "ZarManager could not access the following embedded engines:\n\n{0}\n\nOn Linux, this is usually caused by missing permissions to extract the AppImage or a missing FUSE package.\n\nSOLUTION:\n1. Right-click the .AppImage file, go to 'Properties' and enable 'Allow executing file as program'.\n2. Ensure you have the 'libfuse2' package installed on your system.",

        # === STATUS DO PROCESSAMENTO ===
        "log_extracting_iso": "EXTRACTING ISO",
        "log_extracting_arc": "EXTRACTING ARCHIVE",
        "log_compressing": "COMPRESSING ZAR",
        "log_completed": "COMPLETED",
        "log_failed": "FAILED",
        "log_cancelled": "CANCELLED",

        # === TIPS / TOOLTIPS ===
        "tip_auto": "Smart Cycle: Reads ZIPs, ISOs, or Folders. Runs full pipeline to .zar format.",
        "tip_extract_arc": "Isolated Mode: Extracts archives flatly (no nested folders).",
        "tip_extract": "Isolated Mode: Extracts ISO files (XDVDFS) to a folder.",
        "tip_compress": "Isolated Mode: Compresses an extracted folder to .zar format.",
        "tip_source": "Click to select the folder where your original files are located.",
        "tip_target": "Click to select the folder where the finished files should be saved.",
        "tip_invert": "Quickly inverts the selection of items in the list above.",
        "tip_start": "Starts processing the queue based on the checked items.",
        "tip_pause": "Freezes the current processing. You can resume at any time.",
        "tip_cancel": "Cancels the queue and safely deletes incomplete temporary files.",
        "tip_theme": "Changes the visual theme. Some native palettes may require an app restart.",
        "tip_lang": "Changes the interface and log language in real time."
    }
}

def get_text(lang: str, key: str) -> str:
    if lang not in TRANSLATIONS:
        lang = "pt-br"
    return TRANSLATIONS[lang].get(key, key)