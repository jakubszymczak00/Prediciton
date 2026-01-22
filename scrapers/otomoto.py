from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import json
import re
from utils.cleaning import clean_int
from utils.mapper import get_generation_by_year
from utils.config import TYLKO_NIEUSZKODZONE
try:
    from utils.config import ROK_OD
except ImportError:
    ROK_OD = 2017 

from utils.network import retry
from utils.logger import log
from utils.drivers import random_sleep 

# --- FUNKCJE POMOCNICZE ---

def check_ban_status(driver):
    """
    Sprawdza czy nie ma blokady, ale reaguje TYLKO na twarde błędy.
    """
    try:
        title = driver.title.lower()
        if "429" in title or "too many requests" in driver.page_source.lower()[:200]:
            log.critical("🚨 BŁĄD 429. Pauza 60s...")
            time.sleep(60)
            driver.refresh()
            time.sleep(5)
            return True
        if "just a moment" in title:
            log.warning("🛡️ Captcha. Czekam 15s...")
            time.sleep(15)
    except: pass
    return False

def find_key_recursive(data, target_key):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == target_key: return v
            res = find_key_recursive(v, target_key)
            if res: return res
    elif isinstance(data, list):
        for item in data:
            res = find_key_recursive(item, target_key)
            if res: return res
    return None

# --- PARSERY (Twoje stare, sprawdzone funkcje) ---

@retry(max_retries=3, delay=3)
def extract_list_json(driver):
    # Dodane: sprawdzenie bana
    if check_ban_status(driver): return []
    random_sleep(2, 4)

    script = "try { return document.getElementById('__NEXT_DATA__').innerText; } catch(e) { return null; }"
    raw_json = driver.execute_script(script)
    if not raw_json: return []
    try: full_data = json.loads(raw_json)
    except: return []
    
    results = []
    search_node = find_key_recursive(full_data, 'advertSearch') or find_key_recursive(full_data, 'search')
    if search_node:
        if 'edges' in search_node: results.extend(search_node['edges'])
        elif 'results' in search_node: results.extend(search_node['results'])
        
    if not results:
        urql_state = find_key_recursive(full_data, 'urqlState')
        if urql_state and isinstance(urql_state, dict):
            for key, value in urql_state.items():
                try:
                    inner_data = json.loads(value['data'])
                    node = find_key_recursive(inner_data, 'advertSearch') or find_key_recursive(inner_data, 'search')
                    if node:
                        if 'edges' in node: results.extend(node['edges'])
                        elif 'results' in node: results.extend(node['results'])
                except: continue
    
    if results:
        log.info(f"Extractor: Znaleziono {len(results)} ofert na liście.")
    return results

def parse_html_details(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    details = {}
    
    desc_div = soup.find('div', {'data-testid': 'content-description-section'})
    desc_text = ""
    if desc_div: 
        desc_text = desc_div.get_text(separator=" ", strip=True)
        details['opis'] = desc_text[:5000]
    
    try:
        page_text = soup.get_text()
        date_match = re.search(r'(\d{2}:\d{2}, \d{1,2} [a-zA-Z]+ \d{4})', page_text)
        if date_match: details['zrodlo_aktualizacja'] = date_match.group(1)
        
        text_lower = (page_text + " " + desc_text).lower()
        if "4x4" in text_lower or "4motion" in text_lower or "quattro" in text_lower or "xdrive" in text_lower:
            details['naped'] = "4x4"
        elif "napęd na przednią oś" in text_lower or "przedni napęd" in text_lower or "fwd" in text_lower:
            details['naped'] = "Na przednie koła"
        elif "napęd na tylną oś" in text_lower or "tylny napęd" in text_lower or "rwd" in text_lower:
            details['naped'] = "Na tylne koła"
    except: pass

    params_map = {
        'Marka pojazdu': 'marka', 'Model pojazdu': 'model', 
        'Wersja': 'wersja', 'Generacja': 'generacja', 
        'Rok produkcji': 'rocznik', 'Przebieg': 'przebieg', 
        'Pojemność skokowa': 'pojemnosc', 'Moc': 'moc',
        'Rodzaj paliwa': 'paliwo', 'Skrzynia biegów': 'skrzynia', 
        'Napęd': 'naped', 'Typ napędu': 'naped',
        'Typ nadwozia': 'nadwozie', 'Kolor': 'kolor', 'Kraj pochodzenia': 'kraj',
        'Zarejestrowany w Polsce': 'zarejestrowany', 'Numer rejestracyjny pojazdu': 'nr_rejestracyjny',
        'Stan': 'stan', 'Bezwypadkowy': 'bezwypadkowy'
    }

    for item in soup.find_all(['li', 'div']):
        text = item.get_text(separator="|", strip=True)
        if "|" in text:
            parts = text.split('|')
            if len(parts) >= 2:
                raw_label = parts[0].replace(":", "").strip()
                raw_value = parts[1].strip()
                
                if raw_label in params_map:
                    db_key = params_map[raw_label]
                    if db_key == 'model' and len(raw_value) < 30: details[db_key] = raw_value.title()
                    elif db_key == 'marka': details[db_key] = raw_value.title()
                    elif db_key in ['rocznik', 'przebieg', 'pojemnosc', 'moc']: details[db_key] = clean_int(raw_value)
                    elif raw_value.lower() == 'tak': details[db_key] = 'Tak'
                    else: details[db_key] = raw_value

    return details

@retry(max_retries=2, delay=1)
def extract_offer_page_data(driver):
    details = {}
    try:
        script = """
        try { 
            const json = JSON.parse(document.getElementById('__NEXT_DATA__').innerText); 
            if (json.props && json.props.pageProps && json.props.pageProps.advert) {
                return json.props.pageProps.advert;
            }
            return null;
        } catch(e) { return null; }
        """
        advert_data = driver.execute_script(script)
        
        if advert_data:
            if 'createdAt' in advert_data: details['zrodlo_aktualizacja'] = advert_data['createdAt'].replace('T', ' ').replace('Z', '')
            if 'description' in advert_data: details['opis'] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', advert_data['description'])).strip()[:5000]
            if 'seller' in advert_data: details['typ_sprzedawcy'] = "Dealer" if advert_data['seller'].get('type', '') == 'PROFESSIONAL' else "Prywatny"
            if 'images' in advert_data and 'photos' in advert_data['images']: details['liczba_zdjec'] = len(advert_data['images']['photos'])

            features_list = []
            if 'equipment' in advert_data:
                for group in advert_data['equipment']:
                    if 'values' in group:
                        for val in group['values']:
                            if 'label' in val: features_list.append(val['label'])
            if features_list:
                details['wyposazenie'] = ", ".join(features_list)
                details['liczba_opcji'] = len(features_list)

            raw_params = advert_data.get('details') or advert_data.get('parameters') or []
            
            key_map = {
                'make': 'marka', 'model': 'model', 
                'version': 'wersja', 'generation': 'generacja',
                'year': 'rocznik', 'mileage': 'przebieg', 'fuel_type': 'paliwo', 
                'engine_capacity': 'pojemnosc', 'engine_power': 'moc', 
                'body_type': 'nadwozie', 'color': 'kolor',
                'gearbox': 'skrzynia', 'transmission': 'naped', 'drive': 'naped',
                'country_origin': 'kraj', 'registered': 'zarejestrowany', 
                'registration': 'nr_rejestracyjny', 'no_accident': 'bezwypadkowy'
            }

            if isinstance(raw_params, list):
                for item in raw_params:
                    key = item.get('key')
                    val = item.get('value') or item.get('displayValue')
                    
                    if key in key_map and val:
                        db_col = key_map[key]
                        if db_col == 'model':
                            clean_val = str(val).strip().title()
                            if len(clean_val) < 30: details[db_col] = clean_val
                        elif db_col == 'nr_rejestracyjny':
                            if len(str(val)) > 10: continue
                            details[db_col] = val
                        elif db_col in ['rocznik', 'przebieg', 'pojemnosc', 'moc']: 
                            details[db_col] = clean_int(val)
                        else: 
                            details[db_col] = val
            return details
    except Exception as e: log.warning(f"JSON extract error: {e}")

    log.info("Uzupełnianie z HTML...")
    try:
        html_details = parse_html_details(driver)
        for k, v in html_details.items():
            if v and not details.get(k): details[k] = v
        return details
    except Exception as e:
        log.warning(f"HTML extract error: {e}")
        return details

# --- PĘTLA GŁÓWNA ---

def run_otomoto_scraper(driver, db, stats, marka, model_slug, model_nazwa, kategoria="osobowe", rok_od=None):
    if rok_od is None: rok_od = ROK_OD
    damage_param = "?search%5Bfilter_enum_damaged%5D=0" if TYLKO_NIEUSZKODZONE else ""
    base_url = f"https://www.otomoto.pl/{kategoria}/{marka}/{model_slug}/od-{rok_od}{damage_param}"
    
    log.info(f"Otomoto start [{kategoria}]: {marka} {model_nazwa}")
    page = 1
    
    while True:
        log.info(f"Otomoto page {page}...")
        
        # --- Dodane: Przerwa co 10 stron (ważne dla 429) ---
        if page > 1 and page % 10 == 0:
            log.info("☕ Przerwa anty-ban (30s)...")
            time.sleep(30)

        try:
            driver.get(f"{base_url}&page={page}")
            random_sleep(3, 5) # ZWOLNIENIE
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
        except TimeoutException: break
        
        items = extract_list_json(driver)
        if not items:
            if check_ban_status(driver):
                continue
            break # Koniec ofert
            
        for item in items:
            node = item.get('node') or item
            link = node.get('url')
            try: price_val = float(node['price']['amount']['value'])
            except: price_val = 0
            
            db_data = {
                'url': link, 'platforma': 'otomoto', 'kategoria': kategoria,
                'tytul': f"{marka} {model_nazwa}".strip(), 'cena': int(price_val),
                'marka': marka, 'model': model_nazwa, 'rocznik': 0, 'przebieg': 0, 'opis': ''
            }
            
            params = node.get('parameters', [])
            for p in params:
                k = p.get('key'); v = p.get('value')
                if k == 'year': db_data['rocznik'] = clean_int(v)
                elif k == 'mileage': db_data['przebieg'] = clean_int(v)

            status = db.upsert_oferta(db_data)
            
            # Wchodzimy w ofertę, jeśli nowa, zmieniona cena, LUB jeśli to SEEN ale chcemy uzupełnić dane
            if status in ["INSERT", "UPDATE_PRICE", "SEEN"]:
                driver.get(link)
                random_sleep(2, 4) # ZWOLNIENIE W OFERCIE
                
                try: 
                    # WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    full_details = extract_offer_page_data(driver)
                    
                    if full_details:
                        if full_details.get('marka'): db_data['marka'] = full_details['marka']
                        if full_details.get('model'): db_data['model'] = full_details['model']
                        db_data['tytul'] = f"{db_data.get('marka')} {db_data.get('model')}".strip()

                        for k, v in full_details.items():
                            if v: db_data[k] = v
                        
                        # --- PLAN B: MAPPER ---
                        current_gen = db_data.get('generacja')
                        current_rok = clean_int(db_data.get('rocznik'))
                        
                        if not current_gen and current_rok:
                            mapped_gen = get_generation_by_year(db_data['marka'], db_data['model'], current_rok)
                            if mapped_gen:
                                db_data['generacja'] = mapped_gen

                        db.upsert_oferta(db_data)
                        log.info(f"✅ OK: {db_data.get('cena')} PLN | Gen: {db_data.get('generacja')} | Wer: {db_data.get('wersja')}")
                    
                except Exception as e: log.warning(f"Blad detali: {e}")
                
                if status == "INSERT": stats.add_new()
                elif status != "SEEN": stats.add_price_change()
            
            elif status == "SEEN": stats.add_seen()
            stats.add_processed()
        page += 1