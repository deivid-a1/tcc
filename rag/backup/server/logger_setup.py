import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    LOG_DIR = "logs"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file_path = os.path.join(LOG_DIR, "mcp_server.log")

    log_format = "%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            RotatingFileHandler(
                log_file_path,
                maxBytes=5*1024*1024, 
                backupCount=2
            ),
            logging.StreamHandler()
        ]
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)