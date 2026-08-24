import os
from pathlib import Path
from models.process import ProcessMode
from services.logging_service import logger

class FileService:
    # 🟠 Regras de negócio concentradas
    ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz"}
    ISO_EXTENSIONS = {".iso"}

    @classmethod
    def find_processable_files(cls, directory: str, mode: ProcessMode) -> list[Path]:
        if not directory or not os.path.exists(directory):
            return []
        
        target = Path(directory)
        found_items = []
        
        try:
            for f in target.iterdir():
                is_file = f.is_file()
                suffix = f.suffix.lower()
                
                if mode == ProcessMode.AUTO:
                    # 🟠 Explicitamente aceitamos arquivos comprimidos, ISOs e Diretórios inteiros
                    if (is_file and suffix in cls.ISO_EXTENSIONS | cls.ARCHIVE_EXTENSIONS) or f.is_dir():
                        found_items.append(f)
                elif mode == ProcessMode.EXTRACT_ARC:
                    if is_file and suffix in cls.ARCHIVE_EXTENSIONS:
                        found_items.append(f)
                elif mode == ProcessMode.EXTRACT_ISO:
                    if is_file and suffix in cls.ISO_EXTENSIONS:
                        found_items.append(f)
                elif mode == ProcessMode.COMPRESS:
                    if f.is_dir():
                        found_items.append(f)
                        
        except PermissionError:
            logger.error(f"Permissão negada ao tentar ler: {directory}")
        except OSError as exc:
            logger.error(f"Falha de sistema de ficheiros em {directory}: {exc}")
            
        return sorted(found_items)