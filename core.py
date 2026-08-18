# core.py
import os
import shutil
import subprocess
import sys
import time
import threading
import platform
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. DETECÇÃO DE PLATAFORMA
IS_WINDOWS = platform.system() == "Windows"
BIN_EXTENSION = ".exe" if IS_WINDOWS else ""

# 2. RESOLUÇÃO DE CAMINHO (PyInstaller / Desenvolvimento)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) # Usar _MEIPASS no lugar de sys.executable
else:
    BASE_DIR = Path(__file__).parent.resolve()

BIN_DIR = BASE_DIR / "bin"
# Injeta o .exe automaticamente se estiver no Windows
ZARCHIVE_BIN = BIN_DIR / f"zarchive{BIN_EXTENSION}"
EXTRACT_XISO_BIN = BIN_DIR / f"extract-xiso{BIN_EXTENSION}"

class ZarManagerCore:
    def __init__(self, selected_items: list, target_directory: str, max_workers: int = 1, mode: str = "auto", 
                 log_callback=None, progress_callback=None, status_callback=None):
        self.queue = [Path(p) for p in selected_items]
        self.target_directory = Path(target_directory)
        self.max_workers = max_workers
        self.mode = mode 
        
        self.log_cb = log_callback if log_callback else print
        self.progress_callback = progress_callback if progress_callback else lambda c, t, r: None
        self.status_cb = status_callback if status_callback else lambda n, s: None
        
        self.total_tasks = len(self.queue)
        self.item_progress = {str(item): 0.0 for item in self.queue}
        
        self.cancel_flag = False
        self.pause_event = threading.Event()
        self.pause_event.set() 
        self.active_processes = []
        self.process_lock = threading.Lock()
        self.progress_lock = threading.Lock()

    def log(self, message: str):
        self.log_cb(message)

    def update_status(self, item_name: str, status: str):
        self.status_cb(item_name, status)

    def update_progress(self, item_path: str, value: float):
        with self.progress_lock:
            self.item_progress[item_path] = value
            total_sum = sum(self.item_progress.values())
            overall_ratio = total_sum / self.total_tasks if self.total_tasks > 0 else 0.0
            completed_count = sum(1 for v in self.item_progress.values() if v >= 1.0)
            self.progress_callback(completed_count, self.total_tasks, overall_ratio)

    def verify_environment(self) -> bool:
        # Verifica a existência dos arquivos baseados no Sistema Operacional
        if self.mode in ["auto", "compress"]:
            if not ZARCHIVE_BIN.exists():
                self.log(f"[ERRO CRÍTICO] Motor ZArchive não encontrado em: {ZARCHIVE_BIN}")
                return False
            if not IS_WINDOWS and not os.access(ZARCHIVE_BIN, os.X_OK):
                self.log(f"[ERRO CRÍTICO] ZArchive sem permissão de execução no Linux.")
                return False

        if self.mode in ["auto", "extract"]:
            if not EXTRACT_XISO_BIN.exists():
                self.log(f"[ERRO CRÍTICO] Extractor extract-xiso não encontrado em: {EXTRACT_XISO_BIN}")
                return False
            if not IS_WINDOWS and not os.access(EXTRACT_XISO_BIN, os.X_OK):
                self.log(f"[ERRO CRÍTICO] extract-xiso sem permissão de execução no Linux.")
                return False
            
        self.target_directory.mkdir(parents=True, exist_ok=True)
        return True

    def request_cancel(self):
        self.cancel_flag = True
        self.pause_event.set() 
        with self.process_lock:
            for proc in self.active_processes:
                try: proc.kill()
                except Exception: pass
        self.log("[SISTEMA] Sinal de cancelamento recebido. Abortando processos ativos...")

    def toggle_pause(self) -> bool:
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.log("[SISTEMA] Fila pausada. As tarefas ativas terminarão com segurança.")
            return True
        else:
            self.pause_event.set()
            self.log("[SISTEMA] Fila retomada.")
            return False

    def _run_subprocess_live(self, cmd: list, item_name: str, path_str: str, progress_start: float, progress_range: float):
        # 3. PREVENÇÃO DE JANELAS FANTASMAS NO WINDOWS
        startupinfo = None
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # Esconde a janela do CMD

        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1,
            startupinfo=startupinfo # Aplica a regra
        )
        
        with self.process_lock:
            self.active_processes.append(proc)
        
        linhas_lidas = 0
        estimativa_linhas = 5000 
        
        for line in iter(proc.stdout.readline, ''):
            if self.cancel_flag:
                break
            line_str = line.strip()
            if line_str:
                linhas_lidas += 1
                if linhas_lidas % 50 == 0:
                    self.log(f"[{item_name}] {line_str[:60]}...")
                    progresso_simulado = min(linhas_lidas / estimativa_linhas, 0.95)
                    atual = progress_start + (progresso_simulado * progress_range)
                    self.update_progress(path_str, atual)
                
        proc.stdout.close()
        return_code = proc.wait()
        
        with self.process_lock:
            if proc in self.active_processes:
                self.active_processes.remove(proc)
                
        if self.cancel_flag:
            raise InterruptedError("Processo cancelado pelo usuário.")
            
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)
            
        self.update_progress(path_str, progress_start + progress_range)

    def process_item(self, item_path: Path) -> str:
        self.pause_event.wait() 
        if self.cancel_flag:
            return f"[AVISO] '{item_path.name}' ignorado."

        path_str = str(item_path)
        item_name = item_path.stem if item_path.is_file() else item_path.name
        start_time = time.time()
        
        try:
            self.update_progress(path_str, 0.05)

            if self.mode == "auto":
                extracted_folder = item_path.parent / f"_extracted_{item_name}"
                target_file = self.target_directory / f"{item_name}.zar"
                if extracted_folder.exists(): shutil.rmtree(extracted_folder)
                
                self.update_status(item_name, "Extraindo (XDVDFS)...")
                self._run_subprocess_live([str(EXTRACT_XISO_BIN), "-x", "-d", str(extracted_folder), str(item_path)], item_name, path_str, 0.0, 0.5)
                
                if self.cancel_flag: raise InterruptedError()
                
                self.update_status(item_name, "Comprimindo (.zar)...")
                self._run_subprocess_live([str(ZARCHIVE_BIN), str(extracted_folder), str(target_file)], item_name, path_str, 0.5, 0.49)
                
                self.update_status(item_name, "Limpando resíduos...")
                shutil.rmtree(extracted_folder)

            elif self.mode == "extract":
                target_folder = self.target_directory / item_name
                if target_folder.exists(): shutil.rmtree(target_folder)
                
                self.update_status(item_name, "Descompactando...")
                self._run_subprocess_live([str(EXTRACT_XISO_BIN), "-x", "-d", str(target_folder), str(item_path)], item_name, path_str, 0.0, 0.99)

            elif self.mode == "compress":
                target_file = self.target_directory / f"{item_name}.zar"
                self.update_status(item_name, "Comprimindo...")
                self._run_subprocess_live([str(ZARCHIVE_BIN), str(item_path), str(target_file)], item_name, path_str, 0.0, 0.99)
                
            elapsed_time = time.time() - start_time
            self.update_progress(path_str, 1.0)
            self.update_status(item_name, "CONCLUIDO")
            return f"[SUCESSO] '{item_name}' concluído em {elapsed_time:.2f}s."
            
        except InterruptedError:
            if self.mode == "auto" and 'extracted_folder' in locals() and extracted_folder.exists():
                shutil.rmtree(extracted_folder, ignore_errors=True)
            self.update_progress(path_str, 1.0)
            self.update_status(item_name, "CANCELADO")
            return f"[CANCELADO] '{item_name}' abortado."
            
        except subprocess.CalledProcessError:
            if self.mode == "auto" and 'extracted_folder' in locals() and extracted_folder.exists():
                shutil.rmtree(extracted_folder, ignore_errors=True)
            self.update_progress(path_str, 1.0)
            self.update_status(item_name, "FALHA")
            return f"[ERRO] Falha estrutural em '{item_name}'."
            
        except Exception as e:
            if self.mode == "auto" and 'extracted_folder' in locals() and extracted_folder.exists():
                shutil.rmtree(extracted_folder, ignore_errors=True)
            self.update_progress(path_str, 1.0)
            self.update_status(item_name, "FALHA CRÍTICA")
            return f"[ERRO CRÍTICO] Exceção em '{item_name}': {str(e)}"

    def start_processing(self):
        if not self.queue:
            self.log("[AVISO] Nenhuma tarefa na fila.")
            return

        self.log(f"[SISTEMA] Iniciando processamento de {self.total_tasks} itens.")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_item, item): item for item in self.queue}
            for future in as_completed(futures):
                future.result()
                
        if self.cancel_flag:
            self.log("[SISTEMA] Operação cancelada com sucesso.")
        else:
            self.log("[SISTEMA] Lote finalizado integralmente.")