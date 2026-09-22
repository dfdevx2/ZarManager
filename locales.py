"""Traduções.

O core emite chaves e argumentos (ver core/events.py) e é aqui que se
transformam em texto. Isto substitui o bloco de `msg.replace(...)` que existia
no emit_log e que traduzia mensagens já formatadas, frase a frase.
"""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt-br": {
        # ---------------------------------------------------------- navegação
        "app_title": "ZarManager",
        "nav_auto": "Automático",
        "nav_arc": "Arquivos",
        "nav_iso": "ISO",
        "nav_zar": "Comprimir",
        "nav_settings": "Configurações",
        "nav_about": "Sobre",
        "nav_help": "Ajuda",
        "tip_auto": "Detecta o formato e encadeia as etapas sozinho.",
        "tip_extract_arc": "Só extrai ZIP, RAR e 7z.",
        "tip_extract": "Só extrai imagens de disco.",
        "tip_compress": "Só comprime pastas para .zar.",

        # ------------------------------------------------------ boas-vindas
        "welcome_hero": "ZarManager",
        "welcome_sub": "Extraia, converta e comprima a sua biblioteca sem sair do lugar.",
        "welcome_lang_title": "Em que idioma prefere trabalhar?",
        "welcome_lang_desc": "Pode mudar isto a qualquer momento nas configurações.",
        "welcome_theme_title": "Escolha o visual",
        "welcome_theme_desc": "Clique num cartão para ver o tema aplicado na hora.",
        "welcome_dirs_title": "Onde estão os seus ficheiros?",
        "welcome_dirs_desc": "Opcional agora — dá para definir depois na tela principal.",
        "welcome_step": "Passo {current} de {total}",
        "btn_back": "Voltar",
        "btn_next": "Continuar",
        "btn_start_using": "Começar a usar",
        "btn_skip": "Saltar",

        # -------------------------------------------------------- workspace
        "lbl_source": "Origem",
        "lbl_target": "Destino",
        "btn_browse": "Procurar…",
        "btn_refresh": "Atualizar lista",
        "lbl_items": "Itens encontrados",
        "btn_invert": "Inverter seleção",
        "msg_no_files": "Nenhum ficheiro compatível nesta pasta.",
        "msg_no_source": "Escolha uma pasta de origem para começar.",
        "lbl_selected": "{checked} de {total} selecionados",
        "btn_start": "Iniciar",
        "btn_pause": "Pausar",
        "btn_resume": "Retomar",
        "btn_cancel": "Cancelar",
        "lbl_console": "Registo",
        "btn_clear_console": "Limpar",
        "lbl_progress": "{done} de {total} processados",

        # ------------------------------------------------------------ etapas
        "stage_archive": "A extrair arquivo",
        "stage_xiso": "A extrair imagem",
        "stage_stfs": "A extrair pacote Xbox 360",
        "stage_god": "A reconstruir a imagem (GOD)",
        "stage_zar": "A comprimir (.zar)",
        "stage_rvz": "A converter (.rvz)",
        "stage_chd": "A converter (.chd)",
        "stage_pkg": "A extrair pacote",

        # ------------------------------------------------------------ estados
        "state_queued": "Na fila",
        "state_running": "A processar",
        "state_done": "Concluído",
        "state_failed": "Falhou",
        "state_skipped": "Ignorado",
        "state_cancelled": "Cancelado",

        # ----------------------------------------------------------- formatos
        "fmt_archive": "Arquivo comprimido",
        "fmt_game_dir": "Pasta de jogo",
        "fmt_xiso": "Imagem Xbox (XDVDFS)",
        "fmt_stfs": "Pacote Xbox 360 (XBLA/DLC)",
        "fmt_god": "Games on Demand",
        "fmt_gc_iso": "GameCube",
        "fmt_wii_iso": "Wii",
        "fmt_iso9660": "Imagem ISO9660",
        "fmt_cd_image": "Imagem de CD",
        "fmt_pkg_ps3": "Pacote PS3",
        "fmt_pkg_ps4": "Pacote PS4",
        "fmt_zar": "ZArchive",
        "fmt_rvz": "RVZ",
        "fmt_chd": "CHD",
        "fmt_unknown": "Formato desconhecido",

        # ------------------------------------------------------------ eventos
        "ev_job_start": "A iniciar: {count} item(ns) em modo {mode}.",
        "ev_env_ok": "Ambiente verificado. Motores operacionais.",
        "ev_engine_missing": "Motores em falta: {engines}",
        "ev_engine_optional_missing": "Motores opcionais ausentes: {engines}. Esses formatos vão ser ignorados.",
        "ev_item_start": "{name}: detectado como {fmt}.",
        "ev_item_done": "{name} → {output}",
        "ev_item_failed": "{name}: {error}",
        "ev_item_unknown": "{name}: formato não reconhecido, ignorado.",
        "ev_item_no_route": "{name} ({fmt}): sem motor para este formato ({engines}).",
        "ev_item_nothing_to_do": "{name}: já está no formato final.",
        "ev_item_skip_exists": "{name}: já existe no destino, ignorado.",
        "ev_collision_rename": "Conflito evitado: gravado como {name}.",
        "ev_collision_overwrite": "Substituído: {name}",
        "ev_original_removed": "Original removido: {name}",
        "ev_original_remove_failed": "Não foi possível remover {name}: {error}",
        "ev_target_is_item": "{name} é o próprio diretório de destino e foi ignorado.",
        "ev_cancel_requested": "Cancelamento pedido. A interromper os motores…",
        "ev_paused": "Em pausa.",
        "ev_resumed": "Retomado.",
        "ev_job_done": "Terminado: {completed} concluído(s), {failed} falha(s), {skipped} ignorado(s).",
        "ev_job_cancelled": "Lote cancelado pelo utilizador.",

        # ------------------------------------------------------------- erros
        "err_generic": "Erro inesperado.",
        "err_engine_missing": "O motor {engine} não está disponível.",
        "err_engine_failed": "O motor {engine} terminou com código {code}.",
        "err_elevation_required": "O Windows bloqueou o motor {engine} por falta de privilégios.",
        "err_cancelled": "Operação cancelada.",
        "err_no_route": "Não há como converter {source} em {target}.",

        # ------------------------------------------------------- configurações
        "set_title": "Configurações",
        "set_appearance": "Aparência",
        "set_language": "Idioma",
        "set_theme": "Tema",
        "set_motion": "Reduzir animações",
        "set_motion_hint": "Desliga o salto das pílulas e as transições.",
        "set_audio": "Som",
        "set_sfx": "Efeitos sonoros",
        "set_volume": "Volume",
        "set_test_sound": "Testar",
        "set_performance": "Desempenho",
        "set_workers": "Tarefas em paralelo: {value}",
        "set_workers_hint": "Mais tarefas não significa mais rápido: extrair e comprimir saturam o disco. Entre 2 e 4 costuma ser o ponto ideal.",
        "set_files": "Ficheiros",
        "set_keep_originals": "Manter os originais depois de processar",
        "set_collision": "Quando já existe no destino",
        "collision_ask": "Perguntar",
        "collision_skip": "Ignorar",
        "collision_overwrite": "Substituir",
        "collision_rename": "Renomear (_1)",
        "set_updates": "Atualizações",
        "set_auto_update": "Procurar atualizações ao arrancar",

        # ------------------------------------------------------------- sobre
        "about_title": "Sobre",
        "about_tagline": "Gestor de extração e compressão para bibliotecas de jogos.",
        "about_version": "Versão",
        "about_dev": "Desenvolvimento",
        "about_license": "Licença",
        "about_platform": "Plataforma",
        "about_engines": "Motores incluídos",
        "about_engines_desc": "Cada motor é um programa separado, com a sua própria licença.",
        "about_updated": "Está atualizado",
        "about_update_available": "Há uma versão nova",
        "btn_repo": "Repositório no GitHub",
        "btn_kofi": "Apoiar no Ko-fi",
        "btn_check_update": "Procurar atualizações",
        "btn_troubleshoot": "Resolução de problemas",

        # --------------------------------------------------- troubleshooting
        "ts_title": "Resolução de problemas",
        "ts_sub": "Primeiro o que costuma resolver no seu sistema; o resto fica recolhido.",
        "ts_engines": "Estado dos motores",
        "ts_engines_desc": "Se algum aparecer com ✗, o antivírus provavelmente apagou o ficheiro.",
        "btn_check_engines": "Verificar motores",
        "btn_copy_diag": "Copiar diagnóstico",
        "btn_open_logs": "Abrir pasta de registos",
        "btn_copy_command": "Copiar comando",
        "ts_copied": "Copiado.",
        "ts_engine_native": "Integrado na aplicação",
        "ts_win_title": "Windows: o antivírus apaga os motores",
        "ts_win_body": (
            "O ZarManager é distribuído como pasta portátil. O executável e a pasta "
            "'bin' têm de ficar juntos — mover o .exe para fora quebra o programa.\n\n"
            "Se o Windows Defender apagar algo de dentro de 'bin', adicione a pasta "
            "inteira às exclusões: Segurança do Windows → Proteção contra vírus → "
            "Gerir definições → Adicionar exclusão → Pasta."
        ),
        "ts_lin_title": "Linux: a AppImage não abre",
        "ts_lin_body": (
            "Dê permissão de execução ao ficheiro e confirme que tem o FUSE instalado.\n"
            "Se abrir e não encontrar os motores, verifique se a pasta 'bin' acompanha o binário."
        ),
        "ts_mac_title": "macOS: 'aplicação danificada'",
        "ts_mac_body": (
            "O Gatekeeper marca binários transferidos sem assinatura da Apple. "
            "Retire a quarentena com o comando abaixo e volte a abrir."
        ),
        "ts_perf_title": "Está lento ou o disco satura",
        "ts_perf_body": (
            "Baixe as tarefas em paralelo nas configurações. Extrair e comprimir são "
            "operações limitadas pelo disco, e correr oito ao mesmo tempo costuma ficar "
            "mais lento do que correr duas."
        ),

        # ----------------------------------------------------------- diálogos
        "dlg_collision_title": "Já existe no destino",
        "dlg_collision_desc": "Alguns itens já têm resultado na pasta de destino. O que quer fazer?",
        "btn_skip_existing": "Ignorar existentes",
        "btn_overwrite": "Substituir",
        "btn_rename": "Renomear (_1)",
        "dlg_delete_title": "Apagar os originais?",
        "dlg_delete_desc": "Os originais só são apagados depois de o resultado chegar ao destino.",
        "btn_delete_originals": "Apagar depois de processar",
        "btn_keep_originals": "Manter originais",
        "dlg_done_title": "Concluído",
        "dlg_done_desc": "{completed} item(ns) processado(s) sem erros.",
        "dlg_partial_title": "Concluído com falhas",
        "dlg_partial_desc": "{completed} concluído(s), {failed} com falha. Veja o registo.",
        "dlg_failed_title": "Falhou",
        "dlg_failed_desc": "Nenhum item foi concluído. Veja o registo para o motivo.",
        "dlg_cancelled_title": "Cancelado",
        "dlg_cancelled_desc": "O lote foi interrompido. Nada foi gravado no destino.",
        "dlg_env_title": "Motores em falta",
        "dlg_env_desc": "Faltam estes motores: {engines}\n\nVeja a Resolução de problemas.",
        "av_alert_title": "Motor removido durante a execução",
        "av_alert_msg": (
            "O ficheiro {engine} desapareceu enquanto o ZarManager o usava. "
            "Quase sempre isto é o antivírus a apagá-lo por falso positivo.\n\n"
            "Os seus ficheiros originais não foram tocados."
        ),
        "warn_exit_title": "Há trabalho em curso",
        "warn_exit_msg": "Sair agora cancela o que está a correr. Os originais ficam intactos.",
        "btn_exit_yes": "Sair e cancelar",
        "btn_exit_no": "Continuar a trabalhar",
        "warn_same_dir": "A origem e o destino são a mesma pasta.",
        "warn_target_inside_source": "O destino está dentro da origem. Funciona, mas os resultados vão aparecer na lista de entrada.",
        "msg_err_target": "Defina a pasta de destino.",
        "msg_err_select": "Selecione pelo menos um item.",
        "msg_err_running": "Já existe um processamento a decorrer.",

        # ------------------------------------------------------ atualizações
        "upd_title": "Atualização",
        "upd_checking": "A procurar atualizações…",
        "upd_available": "Versão {version} disponível",
        "upd_latest": "Está na versão mais recente ({version})",
        "upd_error": "Não foi possível falar com o servidor",
        "upd_downloading": "A transferir…",
        "upd_installed": "Versão instalada: {version}",
        "upd_no_asset": "Não há binário para o seu sistema nesta release.",
        "upd_checksum_failed": "O ficheiro transferido não corresponde ao checksum publicado. Atualização abortada.",
        "upd_restart": "Transferência concluída. A reiniciar…",
        "btn_download_update": "Atualizar agora",
        "btn_later": "Mais tarde",
        "btn_close": "Fechar",
    },

    "en": {
        "app_title": "ZarManager",
        "nav_auto": "Automatic",
        "nav_arc": "Archives",
        "nav_iso": "ISO",
        "nav_zar": "Compress",
        "nav_settings": "Settings",
        "nav_about": "About",
        "nav_help": "Help",
        "tip_auto": "Detects the format and chains the steps for you.",
        "tip_extract_arc": "Extracts ZIP, RAR and 7z only.",
        "tip_extract": "Extracts disc images only.",
        "tip_compress": "Compresses folders to .zar only.",

        "welcome_hero": "ZarManager",
        "welcome_sub": "Extract, convert and compress your library without leaving the app.",
        "welcome_lang_title": "Which language do you prefer?",
        "welcome_lang_desc": "You can change this any time in settings.",
        "welcome_theme_title": "Pick a look",
        "welcome_theme_desc": "Click a card to apply the theme right away.",
        "welcome_dirs_title": "Where are your files?",
        "welcome_dirs_desc": "Optional for now — you can set these on the main screen.",
        "welcome_step": "Step {current} of {total}",
        "btn_back": "Back",
        "btn_next": "Continue",
        "btn_start_using": "Get started",
        "btn_skip": "Skip",

        "lbl_source": "Source",
        "lbl_target": "Destination",
        "btn_browse": "Browse…",
        "btn_refresh": "Refresh list",
        "lbl_items": "Items found",
        "btn_invert": "Invert selection",
        "msg_no_files": "No compatible files in this folder.",
        "msg_no_source": "Pick a source folder to get started.",
        "lbl_selected": "{checked} of {total} selected",
        "btn_start": "Start",
        "btn_pause": "Pause",
        "btn_resume": "Resume",
        "btn_cancel": "Cancel",
        "lbl_console": "Log",
        "btn_clear_console": "Clear",
        "lbl_progress": "{done} of {total} processed",

        "stage_archive": "Extracting archive",
        "stage_xiso": "Extracting image",
        "stage_stfs": "Extracting Xbox 360 package",
        "stage_god": "Rebuilding image (GOD)",
        "stage_zar": "Compressing (.zar)",
        "stage_rvz": "Converting (.rvz)",
        "stage_chd": "Converting (.chd)",
        "stage_pkg": "Extracting package",

        "state_queued": "Queued",
        "state_running": "Working",
        "state_done": "Done",
        "state_failed": "Failed",
        "state_skipped": "Skipped",
        "state_cancelled": "Cancelled",

        "fmt_archive": "Compressed archive",
        "fmt_game_dir": "Game folder",
        "fmt_xiso": "Xbox image (XDVDFS)",
        "fmt_stfs": "Xbox 360 package (XBLA/DLC)",
        "fmt_god": "Games on Demand",
        "fmt_gc_iso": "GameCube",
        "fmt_wii_iso": "Wii",
        "fmt_iso9660": "ISO9660 image",
        "fmt_cd_image": "CD image",
        "fmt_pkg_ps3": "PS3 package",
        "fmt_pkg_ps4": "PS4 package",
        "fmt_zar": "ZArchive",
        "fmt_rvz": "RVZ",
        "fmt_chd": "CHD",
        "fmt_unknown": "Unknown format",

        "ev_job_start": "Starting: {count} item(s) in {mode} mode.",
        "ev_env_ok": "Environment verified. Engines operational.",
        "ev_engine_missing": "Missing engines: {engines}",
        "ev_engine_optional_missing": "Optional engines missing: {engines}. Those formats will be skipped.",
        "ev_item_start": "{name}: detected as {fmt}.",
        "ev_item_done": "{name} → {output}",
        "ev_item_failed": "{name}: {error}",
        "ev_item_unknown": "{name}: format not recognised, skipped.",
        "ev_item_no_route": "{name} ({fmt}): no engine for this format ({engines}).",
        "ev_item_nothing_to_do": "{name}: already in its final format.",
        "ev_item_skip_exists": "{name}: already in the destination, skipped.",
        "ev_collision_rename": "Conflict avoided: saved as {name}.",
        "ev_collision_overwrite": "Replaced: {name}",
        "ev_original_removed": "Original removed: {name}",
        "ev_original_remove_failed": "Could not remove {name}: {error}",
        "ev_target_is_item": "{name} is the destination folder itself and was skipped.",
        "ev_cancel_requested": "Cancellation requested. Stopping engines…",
        "ev_paused": "Paused.",
        "ev_resumed": "Resumed.",
        "ev_job_done": "Finished: {completed} done, {failed} failed, {skipped} skipped.",
        "ev_job_cancelled": "Batch cancelled by the user.",

        "err_generic": "Unexpected error.",
        "err_engine_missing": "Engine {engine} is not available.",
        "err_engine_failed": "Engine {engine} exited with code {code}.",
        "err_elevation_required": "Windows blocked engine {engine} for lack of privileges.",
        "err_cancelled": "Operation cancelled.",
        "err_no_route": "No way to convert {source} into {target}.",

        "set_title": "Settings",
        "set_appearance": "Appearance",
        "set_language": "Language",
        "set_theme": "Theme",
        "set_motion": "Reduce motion",
        "set_motion_hint": "Turns off the pill bounce and the transitions.",
        "set_audio": "Sound",
        "set_sfx": "Sound effects",
        "set_volume": "Volume",
        "set_test_sound": "Test",
        "set_performance": "Performance",
        "set_workers": "Parallel tasks: {value}",
        "set_workers_hint": "More tasks is not faster: extracting and compressing saturate the disk. Two to four is usually the sweet spot.",
        "set_files": "Files",
        "set_keep_originals": "Keep originals after processing",
        "set_collision": "When it already exists in the destination",
        "collision_ask": "Ask",
        "collision_skip": "Skip",
        "collision_overwrite": "Replace",
        "collision_rename": "Rename (_1)",
        "set_updates": "Updates",
        "set_auto_update": "Check for updates at startup",

        "about_title": "About",
        "about_tagline": "Extraction and compression manager for game libraries.",
        "about_version": "Version",
        "about_dev": "Development",
        "about_license": "License",
        "about_platform": "Platform",
        "about_engines": "Bundled engines",
        "about_engines_desc": "Each engine is a separate program with its own license.",
        "about_updated": "Up to date",
        "about_update_available": "A new version is available",
        "btn_repo": "GitHub repository",
        "btn_kofi": "Support on Ko-fi",
        "btn_check_update": "Check for updates",
        "btn_troubleshoot": "Troubleshooting",

        "ts_title": "Troubleshooting",
        "ts_sub": "What usually fixes it on your system first; the rest stays collapsed.",
        "ts_engines": "Engine status",
        "ts_engines_desc": "If any shows ✗, your antivirus has probably deleted the file.",
        "btn_check_engines": "Check engines",
        "btn_copy_diag": "Copy diagnostics",
        "btn_open_logs": "Open log folder",
        "btn_copy_command": "Copy command",
        "ts_copied": "Copied.",
        "ts_engine_native": "Built into the app",
        "ts_win_title": "Windows: antivirus deletes the engines",
        "ts_win_body": (
            "ZarManager ships as a portable folder. The executable and the 'bin' folder "
            "must stay together — moving the .exe out breaks the program.\n\n"
            "If Windows Defender removes something from 'bin', exclude the whole folder: "
            "Windows Security → Virus protection → Manage settings → Add exclusion → Folder."
        ),
        "ts_lin_title": "Linux: the AppImage won't open",
        "ts_lin_body": (
            "Make the file executable and confirm FUSE is installed.\n"
            "If it opens but finds no engines, check that the 'bin' folder travels with the binary."
        ),
        "ts_mac_title": "macOS: \"app is damaged\"",
        "ts_mac_body": (
            "Gatekeeper flags downloaded binaries that Apple has not signed. "
            "Clear the quarantine with the command below and open it again."
        ),
        "ts_perf_title": "It's slow or the disk is saturated",
        "ts_perf_body": (
            "Lower the parallel tasks in settings. Extracting and compressing are "
            "disk-bound, and running eight at once is usually slower than running two."
        ),

        "dlg_collision_title": "Already in the destination",
        "dlg_collision_desc": "Some items already have a result in the destination folder. What now?",
        "btn_skip_existing": "Skip existing",
        "btn_overwrite": "Replace",
        "btn_rename": "Rename (_1)",
        "dlg_delete_title": "Delete the originals?",
        "dlg_delete_desc": "Originals are only deleted once the result reaches the destination.",
        "btn_delete_originals": "Delete after processing",
        "btn_keep_originals": "Keep originals",
        "dlg_done_title": "Done",
        "dlg_done_desc": "{completed} item(s) processed without errors.",
        "dlg_partial_title": "Finished with failures",
        "dlg_partial_desc": "{completed} done, {failed} failed. Check the log.",
        "dlg_failed_title": "Failed",
        "dlg_failed_desc": "No item completed. Check the log for the reason.",
        "dlg_cancelled_title": "Cancelled",
        "dlg_cancelled_desc": "The batch was interrupted. Nothing was written to the destination.",
        "dlg_env_title": "Missing engines",
        "dlg_env_desc": "These engines are missing: {engines}\n\nSee Troubleshooting.",
        "av_alert_title": "Engine removed while running",
        "av_alert_msg": (
            "The file {engine} vanished while ZarManager was using it. "
            "This is almost always antivirus deleting it as a false positive.\n\n"
            "Your original files were not touched."
        ),
        "warn_exit_title": "Work in progress",
        "warn_exit_msg": "Leaving now cancels what is running. Originals stay intact.",
        "btn_exit_yes": "Quit and cancel",
        "btn_exit_no": "Keep working",
        "warn_same_dir": "Source and destination are the same folder.",
        "warn_target_inside_source": "The destination is inside the source. It works, but results will show up in the input list.",
        "msg_err_target": "Set the destination folder.",
        "msg_err_select": "Select at least one item.",
        "msg_err_running": "A job is already running.",

        "upd_title": "Update",
        "upd_checking": "Checking for updates…",
        "upd_available": "Version {version} is available",
        "upd_latest": "You're on the latest version ({version})",
        "upd_error": "Could not reach the server",
        "upd_downloading": "Downloading…",
        "upd_installed": "Installed version: {version}",
        "upd_no_asset": "No binary for your system in this release.",
        "upd_checksum_failed": "The downloaded file does not match the published checksum. Update aborted.",
        "upd_restart": "Download complete. Restarting…",
        "btn_download_update": "Update now",
        "btn_later": "Later",
        "btn_close": "Close",
    },
}

DEFAULT_LANGUAGE = "pt-br"
LANGUAGES = {"pt-br": "Português (Brasil)", "en": "English"}


def get_text(lang: str, key: str, fallback: str = "", **args) -> str:
    table = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT_LANGUAGE]
    text = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key) or fallback or key
    if args:
        try:
            return text.format(**args)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def missing_keys() -> dict[str, list[str]]:
    """Chaves presentes no pt-br e ausentes noutro idioma (usado no teste)."""
    reference = set(TRANSLATIONS[DEFAULT_LANGUAGE])
    return {
        lang: sorted(reference - set(table))
        for lang, table in TRANSLATIONS.items()
        if lang != DEFAULT_LANGUAGE
    }
