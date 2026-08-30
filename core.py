import os
import sys
import subprocess
import threading
import platform
import shutil
import time
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class ZarManagerCore:
    def __init__(self, selected_items, target_directory, max_workers, mode, keep_originals, policy_str, log_callback, progress_callback, status_callback):
        self.items = [Path(p) for p in selected_items]
        self.target_dir = Path(target_directory)
        self.max_workers = max_workers
        self.mode = mode
        self.keep_originals = keep_originals
        self.policy = policy_str
        self.log = log_callback
        self.progress_cb = progress_callback
        self.status_cb = status_callback
        
        self.cancel_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.pause_flag.set() 
        
        self.completed_tasks = 0
        self.total_tasks = len(self.items)
        
        self.file_progress = {Path(p).name: 0.0 for p in selected_items}
        self.file_progress_lock = threading.Lock()
        
        if "__compiled__" in globals() or hasattr(sys, 'frozen'):
            self.base_dir = Path(os.path.dirname(__file__)).resolve()
        else:
            self.base_dir = Path(__file__).parent.resolve()
            
        self.bin_dir = self.base_dir / "bin"
        sys_os = platform.system()
        
        if sys_os == "Windows":
            self.xiso_bin = self.bin_dir / "extract-xiso.exe"
            self.zar_bin = self.bin_dir / "zarchive.exe"
            self.bin_7z = self.bin_dir / "7z.exe" 
        elif sys_os == "Darwin":
            self.xiso_bin = self.bin_dir / "extract-xiso-mac"
            self.zar_bin = self.bin_dir / "zarchive-mac"
            self.bin_7z = self.bin_dir / "7zz"
            
            if not self.bin_7z.exists() and shutil.which("7zz"):
                self.bin_7z = Path(shutil.which("7zz"))
            elif not self.bin_7z.exists() and shutil.which("7z"):
                self.bin_7z = Path(shutil.which("7z"))
        else:
            self.xiso_bin = self.bin_dir / "extract-xiso"
            self.zar_bin = self.bin_dir / "zarchive"
            self.bin_7z = self.bin_dir / "7z" 
            
            if not self.bin_7z.exists() and shutil.which("7z"):
                self.bin_7z = Path(shutil.which("7z"))

    def verify_environment(self) -> bool:
        missing = []
        if self.mode in ['auto', 'extract'] and not self.xiso_bin.exists():
            missing.append(f"{self.xiso_bin.name}")
        if self.mode in ['auto', 'compress'] and not self.zar_bin.exists():
            missing.append(f"{self.zar_bin.name}")
            
        has_archives = any(p.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz'] for p in self.items)
        if (self.mode == 'extract_arc' or has_archives) and not self.bin_7z.exists():
            missing.append(f"{self.bin_7z.name}")

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
        actual_workers = min(self.max_workers, len(self.items))
        if actual_workers < 1: 
            actual_workers = 1 
            
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = [executor.submit(self._pipeline, item) for item in self.items]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    self.log(f"[ERRO THREAD] Falha: {str(e)}")

        if self.cancel_flag.is_set():
            self.log("[SISTEMA] Lote abortado pelo utilizador.")
        else:
            self.log("[SISTEMA] Lote concluído com sucesso.")

    def update_file_progress(self, name, progress):
        with self.file_progress_lock:
            self.file_progress[name] = progress
            total_ratio = sum(self.file_progress.values()) / self.total_tasks
        self.progress_cb(self.completed_tasks, self.total_tasks, total_ratio)

    def _handle_collision(self, target_path):
        if not target_path.exists():
            return target_path
            
        if self.policy == "SKIP":
            self.log(f"[SISTEMA] Pulando ficheiro existente: {target_path.name}")
            return None
            
        elif self.policy == "OVERWRITE":
            self.log(f"[SISTEMA] Sobrescrevendo ficheiro existente: {target_path.name}")
            if target_path.is_file():
                try: target_path.unlink()
                except: pass
            else:
                shutil.rmtree(target_path, ignore_errors=True)
            return target_path
            
        else: 
            counter = 1
            stem = target_path.stem
            suffix = target_path.suffix
            parent = target_path.parent
            
            new_target = target_path
            while new_target.exists():
                new_target = parent / f"{stem}_{counter}{suffix}"
                counter += 1
                
            self.log(f"[SISTEMA] Renomeado para evitar conflito: {new_target.name}")
            return new_target

    def _pipeline(self, item_path: Path):
        if self.cancel_flag.is_set():
            self.status_cb(item_path.name, "CANCELADO")
            return

        self.pause_flag.wait()
        original_name = item_path.name
        current_path = item_path
        original_suffix = current_path.suffix.lower()

        def get_step_info(step_id):
            if self.mode == 'auto':
                if original_suffix in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    if step_id == '7z': return 0.0, 0.33
                    if step_id == 'xiso': return 0.33, 0.33
                    if step_id == 'zar': return 0.66, 0.34
                elif original_suffix == '.iso':
                    if step_id == 'xiso': return 0.0, 0.50
                    if step_id == 'zar': return 0.50, 0.50
                else:
                    if step_id == 'zar': return 0.0, 1.0
            return 0.0, 1.0

        try:
            if platform.system() != "Windows":
                if self.bin_7z.exists(): os.chmod(str(self.bin_7z), 0o755)
                if self.xiso_bin.exists(): os.chmod(str(self.xiso_bin), 0o755)
                if self.zar_bin.exists(): os.chmod(str(self.zar_bin), 0o755)

            if current_path.is_file() and current_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                temp_extract_dir = self.target_dir / f"temp_{current_path.stem}"
                
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
                cmd = [str(self.bin_7z), "e", str(current_path), f"-o{temp_extract_dir}", "-y"]
                
                b, w = get_step_info('7z')
                self._run_cmd(cmd, cwd=str(self.target_dir), original_name=original_name, step_name="DESCOMPACTANDO", base_prog=b, weight_prog=w)
                self.update_file_progress(original_name, b + w)
                
                iso_files = list(temp_extract_dir.glob("*.iso"))
                if iso_files:
                    original_stem = Path(original_name).stem
                    target_file = self.target_dir / f"{original_stem}.iso"
                    
                    target_file = self._handle_collision(target_file)
                    if not target_file:
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                        self._finalize_item(original_name, "PULADO")
                        return
                        
                    shutil.move(str(iso_files[0]), str(target_file))
                    current_path = target_file
                else:
                    extracted_folder = self.target_dir / current_path.stem
                    extracted_folder = self._handle_collision(extracted_folder)
                    
                    if not extracted_folder:
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                        self._finalize_item(original_name, "PULADO")
                        return
                        
                    shutil.move(str(temp_extract_dir), str(extracted_folder))
                    current_path = extracted_folder
                
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
                if not self.keep_originals:
                    try: item_path.unlink()
                    except: pass
                
                if self.mode == 'extract_arc':
                    self._finalize_item(original_name, "CONCLUIDO")
                    return

            if self.mode in ['auto', 'extract'] and current_path.is_file() and current_path.suffix.lower() == '.iso':
                iso_extract_dir = self.target_dir / current_path.stem
                
                iso_extract_dir = self._handle_collision(iso_extract_dir)
                if not iso_extract_dir:
                    self._finalize_item(original_name, "PULADO")
                    return
                
                iso_extract_dir.mkdir(parents=True, exist_ok=True)
                
                cmd = [str(self.xiso_bin), "-d", str(iso_extract_dir), "-x", str(current_path)]
                
                b, w = get_step_info('xiso')
                self._run_cmd(cmd, cwd=str(self.target_dir), original_name=original_name, step_name="EXTRAINDO ISO", base_prog=b, weight_prog=w)
                self.update_file_progress(original_name, b + w)
                
                if not self.keep_originals:
                    try: current_path.unlink() 
                    except: pass
                    
                current_path = iso_extract_dir
                
                if self.mode == 'extract':
                    self._finalize_item(original_name, "CONCLUIDO")
                    return

            if self.mode in ['auto', 'compress'] and current_path.is_dir():
                zar_output = self.target_dir / f"{current_path.name}.zar"
                
                zar_output = self._handle_collision(zar_output)
                if not zar_output:
                    self._finalize_item(original_name, "PULADO")
                    return
                    
                cmd = [str(self.zar_bin), str(current_path), str(zar_output)]
                
                b, w = get_step_info('zar')
                self._run_cmd(cmd, cwd=str(self.target_dir), original_name=original_name, step_name="COMPRIMINDO ZAR", base_prog=b, weight_prog=w)
                self.update_file_progress(original_name, b + w)
                
                if not self.keep_originals:
                    shutil.rmtree(current_path, ignore_errors=True)
                
            self._finalize_item(original_name, "CONCLUIDO")

        except Exception as e:
            if "AV_BLOCK|" in str(e):
                raise e 
            self.log(f"[ERRO NO ARQUIVO] {original_name}: {str(e)}")
            self._finalize_item(original_name, "FALHA")

    def _run_cmd(self, cmd_list, cwd=None, original_name=None, step_name="PROCESSANDO", base_prog=0.0, weight_prog=1.0):
        if self.cancel_flag.is_set():
            raise Exception("Cancelado pelo utilizador.")
            
        # --- VERIFICAÇÃO PROFUNDA (ANTI-GHOSTING / ANTIVÍRUS) ---
        binary_path = Path(cmd_list[0])
        if not binary_path.exists():
            raise Exception(f"AV_BLOCK|{binary_path.name}")
            
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        
        if "7z" in str(cmd_list[0]).lower() and "-bsp1" not in cmd_list:
            cmd_list.append("-bsp1")
            
        last_update = 0
        last_line = ""
        
        with subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False, bufsize=0, creationflags=creationflags, cwd=cwd) as process:
            buffer = bytearray()
            while True:
                if self.cancel_flag.is_set():
                    process.kill()
                    raise Exception("Processo abortado.")
                
                char = process.stdout.read(1)
                
                if not char and process.poll() is not None:
                    break
                    
                if char:
                    if char in (b'\r', b'\n'):
                        if buffer:
                            try:
                                clean_line = buffer.decode('utf-8', errors='ignore').strip()
                                buffer.clear()
                                
                                if clean_line:
                                    last_line = clean_line
                                    if original_name and self.status_cb and (time.time() - last_update > 0.15):
                                        perc_match = re.search(r'(\d+)%', clean_line)
                                        if perc_match:
                                            local_perc = float(perc_match.group(1)) / 100.0
                                            current_file_prog = base_prog + (local_perc * weight_prog)
                                            self.update_file_progress(original_name, current_file_prog)
                                            self.status_cb(original_name, f"{step_name} [{perc_match.group(1)}%]")
                                        else:
                                            short_line = clean_line if len(clean_line) < 45 else "..." + clean_line[-42:]
                                            self.status_cb(original_name, f"{step_name} ({short_line})")
                                        last_update = time.time()
                            except: pass
                    else:
                        buffer.extend(char)
                        
            if process.returncode != 0 and not self.cancel_flag.is_set():
                raise Exception(last_line if last_line else f"Falha com código {process.returncode}")

    def _finalize_item(self, name, status):
        self.status_cb(name, status)
        with self.file_progress_lock:
            if status == "CONCLUIDO":
                self.file_progress[name] = 1.0
            self.completed_tasks += 1
            total_ratio = sum(self.file_progress.values()) / self.total_tasks
            self.progress_cb(self.completed_tasks, self.total_tasks, total_ratio)