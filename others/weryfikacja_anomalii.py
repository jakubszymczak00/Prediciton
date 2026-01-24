import sqlite3
import time
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# KONFIGURACJA
DB_NAME = "baza_pojazdow.db"
CENA_MIN_ANOMALIA = 400000  # Sprawdzamy ceny powyżej tej kwoty
ROK_MIN = 2017              # Usuwamy wszystko starsze niż to
ROK_MAX = datetime.date.today().year + 1 # Usuwamy błędy typu rok 2999 (obecny rok + 1 na zapas)

def usun_bledne_roczniki():
    """
    Krok 1: Błyskawiczne czyszczenie bazy z aut spoza zakresu lat.
    Nie wymaga Selenium, działa bezpośrednio na SQL.
    """
    print(f"🧹 KROK 1: Czyszczenie roczników (Zakres: {ROK_MIN} - {ROK_MAX})...")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Sprawdzamy ile tego jest przed usunięciem
    c.execute(f"SELECT COUNT(*) FROM oferty WHERE rocznik < {ROK_MIN} OR rocznik > {ROK_MAX}")
    ilosc = c.fetchone()[0]
    
    if ilosc > 0:
        print(f"   Znaleziono {ilosc} ofert ze złym rocznikiem. Usuwam...")
        c.execute(f"DELETE FROM oferty WHERE rocznik < {ROK_MIN} OR rocznik > {ROK_MAX}")
        conn.commit()
        print(f"   ✅ Usunięto {ilosc} rekordów.")
    else:
        print("   ✅ Roczniki w porządku. Brak ofert do usunięcia.")
        
    conn.close()

def setup_driver():
    options = Options()
    # options.add_argument("--headless") # Odkomentuj, jeśli nie chcesz widzieć okna
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def pobierz_cene_ze_strony(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        
        page_source = driver.page_source.lower()
        
        # 404 Check
        if "nie jest już dostępne" in page_source or "ogłoszenie zakończone" in page_source or "błąd 404" in driver.title.lower():
            return None

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = soup.get_text()

        matches = re.findall(r'(\d[\d\s\.]*)\s*(?:PLN|zł)', text)
        candidates = []
        for m in matches:
            clean = re.sub(r'[^\d]', '', m)
            if clean:
                val = int(clean)
                if 1000 < val < 10000000:
                    candidates.append(val)
        
        if candidates:
            return max(candidates)
            
    except Exception as e:
        print(f"Blad URL: {e}")
        return None
    return None

def napraw_ceny_anomalii():
    """
    Krok 2: Sprawdzanie aut z podejrzanie wysoką ceną.
    """
    print(f"\n🔍 KROK 2: Weryfikacja cen powyżej {CENA_MIN_ANOMALIA} PLN...")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = f"SELECT id, url, cena, marka, model FROM oferty WHERE cena > {CENA_MIN_ANOMALIA}"
    c.execute(query)
    podejrzane = c.fetchall()
    
    if not podejrzane:
        print("   ✅ Brak cenowych anomalii. Baza czysta.")
        conn.close()
        return

    print(f"   Znaleziono {len(podejrzane)} podejrzanych ofert. Uruchamiam przeglądarkę...")
    
    driver = setup_driver()
    stat_usuniete = 0
    stat_poprawione = 0
    stat_ok = 0
    
    try:
        for row in podejrzane:
            db_id, url, stara_cena, marka, model = row
            print(f"   Sprawdzam: {marka} {model} (Baza: {stara_cena} PLN)...")
            
            nowa_cena = pobierz_cene_ze_strony(driver, url)
            
            if nowa_cena is None:
                print(f"     ❌ Ogłoszenie nieaktywne -> USUWANIE")
                c.execute("DELETE FROM oferty WHERE id = ?", (db_id,))
                stat_usuniete += 1
            elif nowa_cena != stara_cena:
                print(f"     📉 Korekta ceny: {stara_cena} -> {nowa_cena} PLN")
                c.execute("UPDATE oferty SET cena = ? WHERE id = ?", (nowa_cena, db_id))
                stat_poprawione += 1
            else:
                print(f"     💎 Cena potwierdzona.")
                stat_ok += 1
                
            conn.commit()
            
    except KeyboardInterrupt:
        print("\nPrzerwano.")
    finally:
        driver.quit()
        conn.close()
        
    print(f"\nRAPORT: Usunięto: {stat_usuniete} | Poprawiono: {stat_poprawione} | Potwierdzono: {stat_ok}")

if __name__ == "__main__":
    # Najpierw szybkie czyszczenie roczników
    usun_bledne_roczniki()
    
    # Potem wolna weryfikacja cen
    napraw_ceny_anomalii()
    
    print("\n💡 Pamiętaj uruchomić 'export_to_csv.py' po zakończeniu!")