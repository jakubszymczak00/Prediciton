import undetected_chromedriver as uc

def init_driver():
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager' # 'eager' jest szybkie, ale timeouty są bezpiecznikiem
    
    # Blokada obrazków
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    # Inicjalizacja
    driver = uc.Chrome(options=options, version_main=142)
    driver.maximize_window()
    
    # --- OBSŁUGA TIMEOUTÓW (NOWOŚĆ) ---
    # Jeśli strona nie załaduje się w 30 sekund -> Rzuć błąd (który obsłuży @retry)
    driver.set_page_load_timeout(30)
    
    # Jeśli skrypt JS na stronie mieli dłużej niż 15 sekund -> Przerwij
    driver.set_script_timeout(15)
    
    # Domyślny czas szukania elementu (zamiast sleep)
    driver.implicitly_wait(5) 
    
    return driver