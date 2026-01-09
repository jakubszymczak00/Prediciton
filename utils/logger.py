import logging
import sys
import os

def setup_logger():
    # Konfiguracja loggera
    logger = logging.getLogger("Scraper")
    logger.setLevel(logging.INFO)
    
    # Format logowania: Czas - Poziom - Wiadomosc
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # Handler 1: Zapis do pliku
    file_handler = logging.FileHandler("scraper.log", encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler 2: Wypisywanie na ekran (konsola)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Inicjalizacja globalna
log = setup_logger()