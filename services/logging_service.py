import logging

class LoggerService:
    @staticmethod
    def setup() -> logging.Logger:
        logger = logging.getLogger("ZarManager")
        logger.propagate = False
        logger.setLevel(logging.INFO)
        
        # 🟠 Evita duplicação de handlers se chamado mais de uma vez
        if not logger.handlers:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            
        return logger

logger = LoggerService.setup()