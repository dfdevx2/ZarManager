# core.py

import sys
import subprocess
import threading
import platform
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class ZarManagerCore:
    def __init__(self, selected_items, target_directory, max_workers, mode, keep_originals, log_callback, progress_callback, status_callback):
        self.items = [Path(p) for p in selected_items]
        self.target_dir = Path(target_directory)
        self.max_workers = max_workers
        self.mode = mode
        self.keep_originals = keep_originals
        self.log = log_callback
        self.progress_cb = progress_callback
        self.status_cb = status_callback
        
        self.cancel_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.pause_flag.set() 
        
        self.completed_tasks = 0
        self.total_tasks = len(self.items)
        
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys._MEIPASS)
        else:
            self.base_dir = Path(__file__).parent.resolve()
            
        self.bin_dir = self.base_dir / "bin"
        sys_os = platform.system()
        
        if sys_os == "Windows":
            self.xiso_bin = self.bin_dir / "extract-xiso.exe"
            self.zar_bin = self.bin_dir / "zarchive.exe"
            self.bin_7z = self.bin_dir / "7z.exe" 
        else:
            self.xiso_bin = self.bin_dir / "extract-xiso"
            self.zar_bin = self.bin_dir / "zarchive"
            self.bin_7z = self.bin_dir / "7z" 
            
            if not self.bin_7z.exists() and shutil.which("7z"):
                self.bin_7z = Path(shutil.which("7z"))

    def verify_environment(self) -> bool:
        missing = []
        if self.mode in ['auto', 'extract'] and not self.xiso_bin.exists():
            missing.append("extract-xiso")
        if self.mode in ['auto', 'compress'] and not self.zar_bin.exists():
            missing.append("zarchive")
            
        has_archives = any(p.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz'] for p in self.items)
        if (self.mode == 'extract_arc' or has_archives) and not self.bin_7z.exists():
            missing.append("7-Zip (7z / 7z.exe)")

        if missing:
            self.log(f"[ERRO AMBIENTAL] Binários ausentes: {', '.join(missing)}")
            return False
        return True

    def toggle_pause(self) -> bool:
        if self.pause_flag.is_set():
            self.pause_flag.clear()
            self.log("[SISTEMA] Processamento em pausa.")
            return True
        else:
            self.pause_flag.set()
            self.log("[SISTEMA] Processamento retomado.")
            return False

    def request_cancel(self):
        self.cancel_flag.set()
        self.pause_flag.set()
        self.log("[SISTEMA] Abortando fila...")

    def start_processing(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._pipeline, item) for item in self.items]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    self.log(f"[ERRO THREAD] Falha: {str(e)}")

        if self.cancel_flag.is_set():
            self.log("[SISTEMA] Lote abortado pelo usuário.")
        else:
            self.log("[SISTEMA] Lote concluído com sucesso.")

    def _pipeline(self, item_path: Path):
        if self.cancel_flag.is_set():
            self.status_cb(item_path.name, "CANCELADO")
            return

        self.pause_flag.wait()
        original_name = item_path.name
        current_path = item_path

        try:
            # ETAPA 1: 7-Zip (Extração Plana)
            if current_path.is_file() and current_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                self.status_cb(original_name, "DESCOMPACTANDO...")
                
                temp_extract_dir = self.target_dir / f"temp_{current_path.stem}"
                cmd = [str(self.bin_7z), "e", str(current_path), f"-o{temp_extract_dir}", "-y"]
                self._run_cmd(cmd)
                
                iso_files = list(temp_extract_dir.glob("*.iso"))
                
                if iso_files:
                    target_file = self.target_dir / iso_files[0].name
                    shutil.move(str(iso_files[0]), str(target_file))
                    current_path = target_file
                else:
                    extracted_folder = self.target_dir / current_path.stem
                    shutil.move(str(temp_extract_dir), str(extracted_folder))
                    current_path = extracted_folder
                
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
                # SÓ APAGA O RAR/ZIP ORIGINAL SE NÃO FOR PARA MANTER
                if not self.keep_originals:
                    try: item_path.unlink()
                    except: pass
                
                if self.mode == 'extract_arc':
                    self._finalize_item(original_name, "CONCLUIDO")
                    return

            # ETAPA 2: Extrair XISO
            if self.mode in ['auto', 'extract'] and current_path.is_file() and current_path.suffix.lower() == '.iso':
                self.status_cb(original_name, "EXTRAINDO ISO...")
                
                if current_path.parent != self.target_dir:
                    new_iso_path = self.target_dir / current_path.name
                    shutil.move(str(current_path), str(new_iso_path))
                    current_path = new_iso_path
                
                cmd = [str(self.xiso_bin), "-x", str(current_path), "-d", str(self.target_dir)]
                self._run_cmd(cmd)
                
                extracted_folder = self.target_dir / current_path.stem
                
                # SÓ APAGA A ISO ORIGINAL SE NÃO FOR PARA MANTER
                if not self.keep_originals:
                    try: current_path.unlink() 
                    except: pass
                    
                current_path = extracted_folder
                
                if self.mode == 'extract':
                    self._finalize_item(original_name, "CONCLUIDO")
                    return

            # ETAPA 3: Comprimir para ZAR
            if self.mode in ['auto', 'compress'] and current_path.is_dir():
                self.status_cb(original_name, "COMPRIMINDO ZAR...")
                zar_output = self.target_dir / f"{current_path.name}.zar"
                
                cmd = [str(self.zar_bin), str(zar_output), str(current_path)]
                self._run_cmd(cmd)
                
                # SÓ APAGA A PASTA EXTRAÍDA SE NÃO FOR PARA MANTER
                if not self.keep_originals:
                    shutil.rmtree(current_path, ignore_errors=True)
                
            self._finalize_item(original_name, "CONCLUIDO")

        except Exception as e:
            self.log(f"[ERRO NO ARQUIVO] {original_name}: {str(e)}")
            self._finalize_item(original_name, "FALHA")

    def _run_cmd(self, cmd_list):
        if self.cancel_flag.is_set():
            raise Exception("Cancelado.")
            
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
        
        while process.poll() is None:
            if self.cancel_flag.is_set():
                process.terminate()
                raise Exception("Processo abortado.")
            process.stdout.readline() 
            
        if process.returncode != 0 and not self.cancel_flag.is_set():
            raise Exception(f"Falha com código {process.returncode}")

    def _finalize_item(self, name, status):
        self.status_cb(name, status)
        with threading.Lock():
            self.completed_tasks += 1
            ratio = self.completed_tasks / self.total_tasks
            self.progress_cb(self.completed_tasks, self.total_tasks, ratio)