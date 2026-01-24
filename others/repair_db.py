import sqlite3
import time
import json
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.drivers import init_driver, random_sleep
from utils.mapper import get_generation_by_year
from utils.cleaning import clean_int
from utils.logger import log

DB_NAME = "baza_pojazdow.db"

def normalize_model_name(marka, model_raw):
    if not model_raw: return ""
    return model_raw.strip().split(',')[0].split('-')[0].title()

# --- AGRESYWNY PARSER MIASTA DLA OTOMOTO ---
def find_otomoto_city(soup, ad_data):
    # Metoda 1: JSON główny
    try:
        if ad_data:
            loc = ad_data.get('location', {})
            if loc and 'city' in loc: return loc['city'].get('name')
            
            seller_loc = ad_data.get('seller', {}).get('location', {})
            if seller_loc and 'city' in seller_loc: return seller_loc['city'].get('name')
    except: pass

    # Metoda 2: Link do mapy (Często to działa najlepiej)
    # Szuka linku <a href="#map">Warszawa</a>
    try:
        map_link = soup.find('a', href="#map")
        if map_link:
            text = map_link.get_text(strip=True)
            return text.split(',')[0].strip() # "Warszawa, Mazowieckie" -> "Warszawa"
    except: pass

    # Metoda 3: Sekcja lokalizacji (Seller Box)
    try:
        # Szukamy kontenerów, które wyglądają na adres
        candidates = soup.find_all(class_=re.compile(r'(seller-box__address|location-text|seller-card__address)'))
        for c in candidates:
            txt = c.get_text(separator=' ', strip=True)
            if txt and len(txt) > 2 and len(txt) < 50:
                # Odsiewamy np. "Pokaż mapę"
                if "map" not in txt.lower():
                    return txt.split(',')[0].strip()
    except: pass

    return None

def parse_otomoto_details(driver):
    details = {}
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 1. Próba JSON
    ad_data = None
    try:
        script = "try { return JSON.parse(document.getElementById('__NEXT_DATA__').innerText).props.pageProps.advert; } catch(e) { return null; }"
        ad_data = driver.execute_script(script)
        
        if ad_data:
            params = ad_data.get('details', []) + ad_data.get('parameters', [])
            key_map = {
                'model': 'model', 'generation': 'generacja', 'version': 'wersja', 
                'transmission': 'naped', 'drive': 'naped'
            }
            for item in params:
                if item.get('key') in key_map: 
                    details[key_map[item.get('key')]] = item.get('value')
    except: pass

    # 2. Szukanie Miasta (Agresywne)
    city = find_otomoto_city(soup, ad_data)
    if city: details['miasto'] = city

    # 3. Fallback HTML dla reszty
    for item in soup.find_all(['li', 'div', 'p']):
        txt = item.get_text(separator='|')
        parts = txt.split('|')
        if len(parts) > 1:
            val = parts[1].strip()
            lbl = parts[0].lower()
            if 'wersja' in lbl and not details.get('wersja'): details['wersja'] = val
            if 'napęd' in lbl and not details.get('naped'): details['naped'] = val
            if 'generacja' in lbl and not details.get('generacja'): details['generacja'] = val

    return details

def parse_autoplac_details(driver):
    details = {}
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # JSON-LD
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            d = json.loads(script.string)
            if isinstance(d, list): d = d[0]
            if 'driveWheelConfiguration' in d: details['naped'] = d['driveWheelConfiguration']
            if 'vehicleConfiguration' in d: details['wersja'] = d['vehicleConfiguration']
        except: pass

    # HTML
    for item in soup.find_all(['li', 'div']):
        txt = item.get_text(separator='|')
        if 'Napęd' in txt: details['naped'] = txt.split('|')[1].strip()
        if 'Wersja' in txt: details['wersja'] = txt.split('|')[1].strip()
        if 'Miasto' in txt: details['miasto'] = txt.split('|')[1].strip()
        
    if not details.get('miasto'):
        loc = soup.find(class_=re.compile("location"))
        if loc: details['miasto'] = loc.get_text(strip=True).split(',')[0]
        
    return details

def run_repair():
    log.info("=== AGRESYWNA NAPRAWA BAZY (Bez limitu czasu) ===")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ZMIANA: Usunąłem warunek czasowy. Bierzemy wszystko co ma braki.
    query = """
        SELECT id, url, platforma, marka, model, rocznik, generacja 
        FROM oferty 
        WHERE is_active = 1 
        AND (
            miasto IS NULL OR miasto = '' OR
            wersja IS NULL OR wersja = '' OR
            naped IS NULL OR naped = ''
        )
        LIMIT 1000 
    """
    # Dodałem LIMIT 1000, żebyś widział postęp, a nie czekał w nieskończoność
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    total = len(rows)
    log.info(f"Znaleziono {total} ofert do naprawy.")
    
    driver = init_driver()
    count = 0
    success = 0

    try:
        for row in rows:
            count += 1
            db_id, url, platforma, marka, model_db, rocznik, generacja_db = row
            
            # Wypiszmy URL, żebyś mógł sprawdzić ręcznie czy tam są dane
            log.info(f"🔍 [{count}/{total}] {marka} {model_db} -> {url}")
            
            try:
                driver.get(url)
                random_sleep(2, 3)
                
                if "429" in driver.title:
                    log.critical("🚨 BŁĄD 429. Pauza 60s...")
                    time.sleep(60)
                    driver.refresh()
                
                new_data = {}
                if platforma == 'otomoto': new_data = parse_otomoto_details(driver)
                elif platforma == 'autoplac': new_data = parse_autoplac_details(driver)
                
                # Debugowanie - co widzi skrypt?
                found_city = new_data.get('miasto', 'BRAK')
                found_ver = new_data.get('wersja', 'BRAK')
                found_naped = new_data.get('naped', 'BRAK')
                
                # Mapper dla generacji
                clean_model = normalize_model_name(marka, new_data.get('model', model_db))
                current_gen = new_data.get('generacja', generacja_db)
                if not current_gen and rocznik:
                    mapped = get_generation_by_year(marka, clean_model, rocznik)
                    if mapped: current_gen = mapped

                # SQL Update
                cursor.execute("""
                    UPDATE oferty SET 
                        model = ?, 
                        generacja = ?, 
                        wersja = COALESCE(?, wersja),
                        naped = COALESCE(?, naped),
                        miasto = COALESCE(?, miasto),
                        ostatnia_aktualizacja = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    clean_model,
                    current_gen,
                    new_data.get('wersja'),
                    new_data.get('naped'),
                    new_data.get('miasto'),
                    db_id
                ))
                conn.commit()
                
                if found_city != 'BRAK' or found_ver != 'BRAK':
                    log.info(f"   ✅ Sukces! Miasto: {found_city} | Wer: {found_ver}")
                    success += 1
                else:
                    log.warning(f"   ⚠️ Nic nowego nie znaleziono.")

            except Exception as e:
                log.warning(f"   ❌ Błąd: {e}")

    except KeyboardInterrupt:
        log.info("Przerwano.")
    finally:
        driver.quit()
        conn.close()
        log.info(f"=== Koniec. Naprawiono skutecznie: {success} ofert. ===")

if __name__ == "__main__":
    run_repair()