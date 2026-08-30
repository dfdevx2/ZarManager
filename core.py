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

# Compilação Global do Regex (Garante altíssima performance no loop de leitura de terminal)
PROGRESS_PATTERN = re.compile(r'(\d+)%')

class ZarManagerCore:
    def __init__(self, selected_items, target_directory, max_workers, mode, keep_originals, policy_str, log_callback, progress_callback, status_callback):
        self.items = [Path(p) for p in selected_items]
        self.target_dir = Path(target_directory)
        self.max_workers = max(1, max_workers)
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
        
        self._resolve_environment()

    def _resolve_environment(self):
        """Mapeamento nativo e limpo de caminhos, compatível com Nuitka, PyInstaller e Raw Python."""
        if "__compiled__" in globals() or hasattr(sys, 'frozen'):
            self.base_dir = Path(os.path.dirname(sys.executable)).resolve() if platform.system() == "Windows" else Path(sys.argv[0]).parent.resolve()
        else:
            self.base_dir = Path(__file__).parent.resolve()
            
        self.bin_dir = self.base_dir / "bin"
        sys_os = platform.system()
        
        if sys_os == "Windows":
            self.xiso_bin = self.bin_dir / "extract-xiso.exe"
            self.zar_bin = self.bin_dir / "zarchive.exe"
            self.bin_7z = self.bin_dir / "7z.exe"
        else:
            # Arquitetura UNIX (macOS e Linux)
            mac_suffix = "-mac" if sys_os == "Darwin" else ""
            self.xiso_bin = self.bin_dir / f"extract-xiso{mac_suffix}"
            self.zar_bin = self.bin_dir / f"zarchive{mac_suffix}"
            
            # Resolução Inteligente do 7z no UNIX
            local_7z = self.bin_dir / ("7zz" if sys_os == "Darwin" else "7z")
            if local_7z.exists():
                self.bin_7z = local_7z
            else:
                system_7z = shutil.which("7zz") or shutil.which("7z")
                self.bin_7z = Path(system_7z) if system_7z else local_7z

    def verify_environment(self) -> bool:
        missing = []
        if self.mode in ['auto', 'extract'] and not self.xiso_bin.exists():
            missing.append(self.xiso_bin.name)
        if self.mode in ['auto', 'compress'] and not self.zar_bin.exists():
            missing.append(self.zar_bin.name)
            
        has_archives = any(p.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz'] for p in self.items)
        if (self.mode == 'extract_arc' or has_archives) and not self.bin_7z.exists():
            missing.append(self.bin_7z.name)

        if missing:
            self.log(f"[ERRO AMBIENTAL] Motores ausentes: {', '.join(missing)}")
            return False
            
        # Garante permissões de execução nativas em sistemas UNIX
        if platform.system() != "Windows":
            for bin_path in [self.bin_7z, self.xiso_bin, self.zar_bin]:
                if bin_path.exists():
                    os.chmod(str(bin_path), 0o755)
                    
        return True

    def toggle_pause(self) -> bool:
        if self.pause_flag.is_set():
            self.pause_flag.clear()
            self.log("[SISTEMA] Processamento em pausa.")
            return True
        self.pause_flag.set()
        self.log("[SISTEMA] Processamento retomado.")
        return False

    def request_cancel(self):
        self.cancel_flag.set()
        self.pause_flag.set()
        self.log("[SISTEMA] Abortando fila de forma segura...")

    def start_processing(self):
        actual_workers = min(self.max_workers, len(self.items))
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            futures = [executor.submit(self._pipeline, item) for item in self.items]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    self.log(f"[ERRO FATAL THREAD] {str(e)}")

        if self.cancel_flag.is_set():
            self.log("[SISTEMA] Tarefa abortada pelo utilizador.")
        else:
            self.log("[SISTEMA] Lote concluído com sucesso.")

    def update_file_progress(self, name, progress):
        with self.file_progress_lock:
            self.file_progress[name] = progress
            total_ratio = sum(self.file_progress.values()) / self.total_tasks
        self.progress_cb(self.completed_tasks, self.total_tasks, total_ratio)

    def _handle_collision(self, target_path: Path):
        if not target_path.exists():
            return target_path
            
        if self.policy == "SKIP":
            self.log(f"[SISTEMA] Ignorado (já existe): {target_path.name}")
            return None
            
        if self.policy == "OVERWRITE":
            self.log(f"[SISTEMA] Sobrescrito: {target_path.name}")
            if target_path.is_file() or target_path.is_symlink():
                target_path.unlink(missing_ok=True)
            else:
                shutil.rmtree(target_path, ignore_errors=True)
            return target_path
            
        # AUTO-RENAME (O(1) lookups via set se necessário no futuro, mas sequencial serve bem)
        counter = 1
        stem, suffix, parent = target_path.stem, target_path.suffix, target_path.parent
        new_target = target_path
        
        while new_target.exists():
            new_target = parent / f"{stem}_{counter}{suffix}"
            counter += 1
            
        self.log(f"[SISTEMA] Colisão evitada (Renomeado): {new_target.name}")
        return new_target

    def _get_step_weights(self, original_suffix: str, step_id: str):
        """Mapeia o peso matemático de cada etapa no progresso total."""
        if self.mode != 'auto':
            return 0.0, 1.0
            
        if original_suffix in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            weights = {'7z': (0.0, 0.33), 'xiso': (0.33, 0.33), 'zar': (0.66, 0.34)}
        elif original_suffix == '.iso':
            weights = {'xiso': (0.0, 0.50), 'zar': (0.50, 0.50)}
        else:
            weights = {'zar': (0.0, 1.0)}
            
        return weights.get(step_id, (0.0, 1.0))

    def _pipeline(self, item_path: Path):
        if self.cancel_flag.is_set():
            self._finalize_item(item_path.name, "CANCELADO")
            return

        self.pause_flag.wait()
        original_name = item_path.name
        current_path = item_path
        original_suffix = current_path.suffix.lower()

        try:
            # 1. DESCOMPACTAÇÃO
            if current_path.is_file() and current_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                temp_extract_dir = self.target_dir / f"temp_{current_path.stem}"
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
                cmd = [str(self.bin_7z), "e", str(current_path), f"-o{temp_extract_dir}", "-y"]
                b, w = self._get_step_weights(original_suffix, '7z')
                
                self._run_cmd(cmd, cwd=str(self.target_dir), original_name=original_name, step_name="DESCOMPACTANDO", base_prog=b, weight_prog=w)
                self.update_file_progress(original_name, b + w)
                
                iso_files = list(temp_extract_dir.glob("*.iso"))
                if iso_files:
                    target_file = self._handle_collision(self.target_dir / f"{current_path.stem}.iso")
                    if not target_file:
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                        return self._finalize_item(original_name, "PULADO")
                        
                    shutil.move(str(iso_files[0]), str(target_file))
                    current_path = target_file
                else:
                    extracted_folder = self._handle_collision(self.target_dir / current_path.stem)
                    if not extracted_folder:
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                        return self._finalize_item(original_name, "PULADO")
                        
                    shutil.move(str(temp_extract_dir), str(extracted_folder))
                    current_path = extracted_folder
                
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
                if not self.keep_originals:
                    item_path.unlink(missing_ok=True)
                
                if self.mode == 'extract_arc':
                    return self._finalize_item(original_name, "CONCLUIDO")

            # 2. EXTRAÇÃO DE ISO
            if self.mode in ['auto', 'extract'] and current_path.is_file() and current_path.suffix.lower() == '.iso':
                iso_extract_dir = self._handle_collision(self.target_dir / current_path.stem)
                
                if not iso_extract_dir:
                    return self._finalize_item(original_name, "PULADO")
                
                iso_extract_dir.mkdir(parents=True, exist_ok=True)
                cmd = [str(self.xiso_bin), "-d", str(iso_extract_dir), "-x", str(current_path)]
                b, w = self._get_step_weights(original_suffix, 'xiso')
                
                self._run_cmd(cmd, cwd=str(self.target_dir), original_name=original_name, step_name="EXTRAINDO ISO", base_prog=b, weight_prog=w)
                self.update_file_progress(original_name, b + w)
                
                if not self.keep_originals:
                    current_path.unlink(missing_ok=True)
                    
                current_path = iso_extract_dir
                
                if self.mode == 'extract':
                    return self._finalize_item(original_name, "CONCLUIDO")

            # 3. COMPRESSÃO PARA ZAR
            if self.mode in ['auto', 'compress'] and current_path.is_dir():
                zar_output = self._handle_collision(self.target_dir / f"{current_path.name}.zar")
                
                if not zar_output:
                    return self._finalize_item(original_name, "PULADO")
                    
                cmd = [str(self.zar_bin), str(current_path), str(zar_output)]
                b, w = self._get_step_weights(original_suffix, 'zar')
                
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
            
        binary_path = Path(cmd_list[0])
        if not binary_path.exists():
            raise Exception(f"AV_BLOCK|{binary_path.name}")
            
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        
        if "7z" in binary_path.name.lower() and "-bsp1" not in cmd_list:
            cmd_list.append("-bsp1")
            
        last_update = 0
        last_line = ""
        
        try:
            with subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False, bufsize=0, creationflags=creationflags, cwd=cwd) as process:
                buffer = bytearray()
                
                while True:
                    if self.cancel_flag.is_set():
                        process.terminate()
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
                                        now = time.time()
                                        
                                        # Limitador de refresh para poupar GPU/CPU na UI (10 FPS)
                                        if original_name and self.status_cb and (now - last_update > 0.1):
                                            perc_match = PROGRESS_PATTERN.search(clean_line)
                                            if perc_match:
                                                local_perc = float(perc_match.group(1)) / 100.0
                                                current_file_prog = base_prog + (local_perc * weight_prog)
                                                self.update_file_progress(original_name, current_file_prog)
                                                self.status_cb(original_name, f"{step_name} [{perc_match.group(1)}%]")
                                            else:
                                                short_line = clean_line if len(clean_line) < 45 else "..." + clean_line[-42:]
                                                self.status_cb(original_name, f"{step_name} ({short_line})")
                                            last_update = now
                                except Exception: 
                                    pass
                        else:
                            buffer.extend(char)
                            
                # TÉCNICA DE ALTO NÍVEL: O 7-Zip devolve Código 1 para Avisos Inofensivos.
                if process.returncode not in [0, 1] and not self.cancel_flag.is_set():
                    raise Exception(last_line if last_line else f"Falha com código {process.returncode}")

        except OSError as e:
            # TÉCNICA DE ALTO NÍVEL: Captura limpa do erro UAC do Windows (WinError 740)
            if getattr(e, 'winerror', None) == 740:
                raise Exception("O Windows bloqueou a ação (Falta de privilégios). Feche e abra o ZarManager como Administrador.")
            else:
                raise Exception(f"Erro de sistema no motor ({binary_path.name}): {str(e)}")

    def _finalize_item(self, name, status):
        self.status_cb(name, status)
        with self.file_progress_lock:
            if status == "CONCLUIDO":
                self.file_progress[name] = 1.0
            self.completed_tasks += 1
            total_ratio = sum(self.file_progress.values()) / self.total_tasks
        self.progress_cb(self.completed_tasks, self.total_tasks, total_ratio)