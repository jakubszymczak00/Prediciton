from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

def init_driver():
    options = Options()
    # Ukrywanie cech bota
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Fake User-Agent (wyglądamy jak zwykły Windows)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Skrypt JS usuwający flagę webdrivera
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def random_sleep(min_seconds=2, max_seconds=5):
    """
    Usypia wątek na losowy czas. 
    Kluczowe dla unikania 429.
    """
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)