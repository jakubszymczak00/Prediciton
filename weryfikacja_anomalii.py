import sqlite3
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# KONFIGURACJA
DB_NAME = "baza_pojazdow.db"
PROG_CENOWY = 400000  # Sprawdzamy wszystko powyżej tej kwoty

def setup_driver():
    options = Options()
    # options.add_argument("--headless") # Odkomentuj, jeśli nie chcesz widzieć okna
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Blokowanie obrazków przyspiesza weryfikację
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def pobierz_cene_ze_strony(driver, url):
    """
    Probuje wyciagnac cene ze strony.
    Zwraca (int) cene lub None jesli nie znaleziono/ogloszenie nieaktywne.
    """
    try:
        driver.get(url)
        time.sleep(2) # Krotka pauza na zaladowanie JS
        
        page_source = driver.page_source.lower()
        
        # 1. Sprawdzenie czy ogłoszenie wygasło (Otomoto/Autoplac)
        if "nie jest już dostępne" in page_source or "ogłoszenie zakończone" in page_source or "błąd 404" in driver.title.lower():
            return None

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = soup.get_text()

        # 2. Specyficzne szukanie ceny (bardziej restrykcyjne niz scraper)
        # Szukamy cyfr w poblizu slowa "PLN" lub "zł", unikajac nr telefonu
        
        # Metoda Regex dla Otomoto/Autoplac
        # Szuka ciagow typu: 45 900 PLN, 1.200.000 zł
        matches = re.findall(r'(\d[\d\s\.]*)\s*(?:PLN|zł)', text)
        
        candidates = []
        for m in matches:
            # Czyscimy spacje i kropki
            clean = re.sub(r'[^\d]', '', m)
            if clean:
                val = int(clean)
                # Odrzucamy liczby za male (np "1 PLN") i numery telefonow (zazwyczaj 9 cyfr, > 10mln)
                if 1000 < val < 10000000:
                    candidates.append(val)
        
        if candidates:
            # Zazwyczaj cena to najwieksza liczba na stronie (ale mniejsza niz nr telefonu)
            # Lub pierwsza znaleziona w sekcji ceny. Bierzemy max z sensownego zakresu.
            return max(candidates)
            
    except Exception as e:
        print(f"Blad podczas weryfikacji URL: {e}")
        return None
        
    return None

def napraw_baze():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Pobieramy podejrzane rekordy
    query = f"SELECT id, url, cena, marka, model FROM oferty WHERE cena > {PROG_CENOWY}"
    c.execute(query)
    podejrzane = c.fetchall()
    
    if not podejrzane:
        print(f"✅ Brak aut powyżej {PROG_CENOWY} PLN. Baza czysta.")
        return

    print(f"🔍 Znaleziono {len(podejrzane)} podejrzanych ofert (> {PROG_CENOWY} PLN). Rozpoczynam weryfikację...")
    
    driver = setup_driver()
    usuniete = 0
    poprawione = 0
    potwierdzone = 0
    
    try:
        for row in podejrzane:
            db_id, url, stara_cena, marka, model = row
            
            print(f"\nSprawdzam ID {db_id}: {marka} {model} (Baza: {stara_cena} PLN)")
            
            nowa_cena = pobierz_cene_ze_strony(driver, url)
            
            if nowa_cena is None:
                # Ogloszenie nie istnieje -> USUWAMY
                print(f"❌ Ogłoszenie nieaktywne lub błąd 404. Usuwam z bazy.")
                c.execute("DELETE FROM oferty WHERE id = ?", (db_id,))
                usuniete += 1
                
            elif nowa_cena != stara_cena:
                # Cena jest inna -> AKTUALIZUJEMY
                if nowa_cena < PROG_CENOWY:
                    print(f"📉 Znaleziono błąd! Nowa cena to {nowa_cena} PLN (było {stara_cena}). Aktualizuję.")
                    c.execute("UPDATE oferty SET cena = ? WHERE id = ?", (nowa_cena, db_id))
                    poprawione += 1
                else:
                    # Cena nadal wysoka, ale inna
                    print(f"🔄 Cena zmieniona na {nowa_cena} PLN (nadal wysoka). Aktualizuję.")
                    c.execute("UPDATE oferty SET cena = ? WHERE id = ?", (nowa_cena, db_id))
                    poprawione += 1
            
            else:
                # Cena taka sama -> PRAWDZIWE LUKSUSOWE AUTO?
                print(f"💎 Cena potwierdzona ({nowa_cena} PLN). To prawdopodobnie luksusowe auto.")
                potwierdzone += 1
                
            conn.commit() # Zapisujemy po kazdym kroku
            
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika.")
    finally:
        driver.quit()
        conn.close()
        
    print("\n" + "="*40)
    print(f"RAPORT KOŃCOWY:")
    print(f"🗑️ Usunięto (nieaktywne): {usuniete}")
    print(f"🔧 Naprawiono ceny:      {poprawione}")
    print(f"💎 Potwierdzono (drogie): {potwierdzone}")
    print("="*40)
    print("💡 Pamiętaj uruchomić 'export_to_csv.py' aby zobaczyć zmiany w dashboardzie!")

if __name__ == "__main__":
    napraw_baze()