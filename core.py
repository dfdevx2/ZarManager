# core.py
# Motor de Processamento XDVDFS & ZArchive (Compatível com Executável PyInstaller)

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Determina o diretório base considerando se está rodando via script ou executável compilado
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.resolve()

BIN_DIR = BASE_DIR / "bin"
ZARCHIVE_BIN = BIN_DIR / "zarchive"
EXTRACT_XISO_BIN = BIN_DIR / "extract-xiso"

class ZarManagerCore:
    def __init__(self, source_directory: str, target_directory: str, max_workers: int = 1, mode: str = "auto", log_callback=None, progress_callback=None):
        self.source_dir = Path(source_directory)
        self.target_directory = Path(target_directory)
        self.max_workers = max_workers
        self.mode = mode # Opções: "auto", "extract", "compress"
        self.queue = []
        
        self.log_cb = log_callback if log_callback else print
        self.progress_cb = progress_callback if progress_callback else lambda current, total: None
        
        self.completed_tasks = 0
        self.total_tasks = 0

    def log(self, message: str):
        self.log_cb(message)

    def verify_environment(self) -> bool:
        if self.mode in ["auto", "compress"] and (not ZARCHIVE_BIN.exists() or not os.access(ZARCHIVE_BIN, os.X_OK)):
            self.log(f"[ERRO CRÍTICO] Motor ZArchive ausente em: {ZARCHIVE_BIN}")
            return False
            
        if self.mode in ["auto", "extract"] and (not EXTRACT_XISO_BIN.exists() or not os.access(EXTRACT_XISO_BIN, os.X_OK)):
            self.log(f"[ERRO CRÍTICO] Extractor extract-xiso ausente em: {EXTRACT_XISO_BIN}")
            return False
            
        if not self.source_dir.exists():
            self.log(f"[ERRO CRÍTICO] Diretório de origem não encontrado: {self.source_dir}")
            return False
            
        self.target_directory.mkdir(parents=True, exist_ok=True)
        return True

    def scan_files(self):
        self.log(f"[SISTEMA] Escaneando diretório de origem...")
        
        if self.mode in ["auto", "extract"]:
            for item in self.source_dir.glob("*.iso"):
                if item.is_file(): self.queue.append(item)
            for item in self.source_dir.rglob("*.iso"):
                if item.is_file() and item not in self.queue: self.queue.append(item)
                
        elif self.mode == "compress":
            for item in self.source_dir.iterdir():
                if item.is_dir(): self.queue.append(item)
                
        self.total_tasks = len(self.queue)
        self.log(f"[SISTEMA] Mapeamento concluído. {self.total_tasks} itens localizados.")

    def process_item(self, item_path: Path) -> str:
        item_name = item_path.stem if item_path.is_file() else item_path.name
        start_time = time.time()
        
        try:
            if self.mode == "auto":
                extracted_folder = self.source_dir / f"_extracted_{item_name}"
                target_file = self.target_directory / f"{item_name}.zar"
                if extracted_folder.exists(): shutil.rmtree(extracted_folder)
                
                self.log(f"[EXTRAÇÃO] Lendo setores de: {item_name}...")
                subprocess.run([str(EXTRACT_XISO_BIN), "-x", "-d", str(extracted_folder), str(item_path)], check=True, capture_output=True, text=True)
                
                self.log(f"[COMPRESSÃO] Escrevendo .zar para: {item_name}...")
                subprocess.run([str(ZARCHIVE_BIN), str(extracted_folder), str(target_file)], check=True, capture_output=True, text=True)
                shutil.rmtree(extracted_folder)

            elif self.mode == "extract":
                target_folder = self.target_directory / item_name
                if target_folder.exists(): shutil.rmtree(target_folder)
                
                self.log(f"[EXTRAÇÃO] Descompactando XDVDFS: {item_name}...")
                subprocess.run([str(EXTRACT_XISO_BIN), "-x", "-d", str(target_folder), str(item_path)], check=True, capture_output=True, text=True)

            elif self.mode == "compress":
                target_file = self.target_directory / f"{item_name}.zar"
                self.log(f"[COMPRESSÃO] Gerando bloco iterativo .zar para: {item_name}...")
                subprocess.run([str(ZARCHIVE_BIN), str(item_path), str(target_file)], check=True, capture_output=True, text=True)
                
            elapsed_time = time.time() - start_time
            return f"[SUCESSO] Operação em '{item_name}' concluída em {elapsed_time:.2f} segundos."
            
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else e.stdout
            if self.mode == "auto" and 'extracted_folder' in locals() and extracted_folder.exists():
                shutil.rmtree(extracted_folder, ignore_errors=True)
            return f"[ERRO] Falha estrutural em '{item_name}': {error_output.strip()}"
        except Exception as e:
            if self.mode == "auto" and 'extracted_folder' in locals() and extracted_folder.exists():
                shutil.rmtree(extracted_folder, ignore_errors=True)
            return f"[ERRO CRÍTICO] Exceção em '{item_name}': {str(e)}"

    def start_processing(self):
        if not self.queue:
            self.log("[AVISO] A fila está vazia. Verifique os diretórios.")
            return

        self.log(f"[SISTEMA] Iniciando pool de threads com {self.max_workers} núcleos alocados.")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_item, item): item for item in self.queue}
            
            for future in as_completed(futures):
                result = future.result()
                self.log(result)
                self.completed_tasks += 1
                self.progress_cb(self.completed_tasks, self.total_tasks)
                
        self.log("[SISTEMA] Rotina de lote finalizada com êxito.")