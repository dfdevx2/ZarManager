# locales.py
# Gerenciamento expandido de idiomas do ZarManager

TRANSLATIONS = {
    "pt-br": {
        "app_title": "ZarManager - Xbox 360 XDVDFS & ZArchive",
        "tab_auto": "Automatizado",
        "tab_extract": "Apenas Extrair",
        "tab_compress": "Apenas Comprimir",
        "tab_settings": "Configurações",
        "tab_about": "Sobre o Projeto",
        "lbl_source": "Diretório de Origem (ISOs):",
        "lbl_target": "Diretório de Destino (Saída):",
        "btn_browse": "Selecionar Pasta",
        "btn_start": "Iniciar Processamento",
        "btn_stop": "Cancelar Operação",
        "lbl_workers": "Processos Simultâneos (Threads):",
        "lbl_language": "Idioma do Sistema:",
        "lbl_theme": "Tema Visual:",
        "log_ready": "[SISTEMA] Motor gráfico inicializado. Aguardando parâmetros...",
        "msg_select_dir": "Selecione um diretório válido.",
        "about_title": "ZarManager v1.0",
        "about_desc": "Ferramenta definitiva para extração estrutural (XDVDFS) e compressão aleatória (ZArchive) focada no emulador Xenia.",
        "about_tutorial": "TUTORIAL RÁPIDO:\n1. Vá em Configurações e defina o limite de Threads (recomendado: metade dos seus núcleos lógicos).\n2. Selecione a aba desejada (Automático é recomendado para ISOs brutas).\n3. Selecione a pasta de Origem e a de Destino.\n4. Clique em Iniciar. O sistema fará a limpeza temporária automaticamente.",
        "btn_github": "Acessar Repositório (GitHub)",
        "lbl_update": "Update Tracker: Versão mais recente instalada."
    },
    "en": {
        "app_title": "ZarManager - Xbox 360 XDVDFS & ZArchive",
        "tab_auto": "Automated (All-in-One)",
        "tab_extract": "Extract Only",
        "tab_compress": "Compress Only",
        "tab_settings": "Settings",
        "tab_about": "About Project",
        "lbl_source": "Source Directory (ISOs):",
        "lbl_target": "Target Directory (Output):",
        "btn_browse": "Browse Folder",
        "btn_start": "Start Processing",
        "btn_stop": "Cancel Operation",
        "lbl_workers": "Simultaneous Processes (Threads):",
        "lbl_language": "System Language:",
        "lbl_theme": "Visual Theme:",
        "log_ready": "[SYSTEM] GUI Engine initialized. Awaiting parameters...",
        "msg_select_dir": "Please select a valid directory.",
        "about_title": "ZarManager v1.0",
        "about_desc": "Definitive tool for structural extraction (XDVDFS) and random-access compression (ZArchive) focused on the Xenia emulator.",
        "about_tutorial": "QUICK TUTORIAL:\n1. Go to Settings and define the Thread limit (recommended: half of your logical cores).\n2. Select the desired tab (Automated is recommended for raw ISOs).\n3. Select the Source and Target folders.\n4. Click Start. The system will handle temporary cleaning automatically.",
        "btn_github": "Visit Repository (GitHub)",
        "lbl_update": "Update Tracker: Latest version installed."
    }
}

def get_text(lang_code: str, key: str) -> str:
    try:
        return TRANSLATIONS[lang_code][key]
    except KeyError:
        return TRANSLATIONS["en"].get(key, f"[{key}]")