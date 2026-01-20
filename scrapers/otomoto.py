from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import json
import re
from utils.cleaning import clean_int
from utils.config import ROK_OD, TYLKO_NIEUSZKODZONE
from utils.network import retry
from utils.logger import log

@retry(max_retries=3, delay=3)
def extract_list_json(driver):
    script = """
    try { 
        const json = JSON.parse(document.getElementById('__NEXT_DATA__').innerText); 
        return json.props.pageProps.urqlState; 
    } catch(e) { return null; }
    """
    urql_cache = driver.execute_script(script)
    if not urql_cache: 
        return []

    results = []
    for key, value in urql_cache.items():
        try:
            data = json.loads(value['data'])
            if 'advertSearch' in data and 'edges' in data['advertSearch']: 
                results.extend(data['advertSearch']['edges'])
            elif 'search' in data and 'results' in data['search']: 
                results.extend(data['search']['results'])
        except: 
            continue
            
    return results

@retry(max_retries=2, delay=1)
def parse_html_description_only(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        desc_div = soup.find('div', {'data-testid': 'content-description-section'})
        if desc_div:
            return desc_div.get_text(separator=" ", strip=True)[:5000]
    except:
        pass
    return ""

def run_otomoto_scraper(driver, db, stats, marka, model_slug, model_nazwa):
    damage_param = "?search%5Bfilter_enum_damaged%5D=0" if TYLKO_NIEUSZKODZONE else ""
    base_url = f"https://www.otomoto.pl/osobowe/{marka}/{model_slug}/od-{ROK_OD}{damage_param}"
    
    log.info(f"Otomoto start: {marka} {model_nazwa}")
    page = 1
    
    while True:
        separator = "&" if "?" in base_url else "?"
        current_url = f"{base_url}{separator}page={page}"
        log.info(f"Otomoto page {page}...")
        
        try:
            driver.get(current_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
        except TimeoutException:
            log.warning("Otomoto timeout.")
            break
        
        items = extract_list_json(driver)
        if not items:
            log.info("No items found or end of pages.")
            break
            
        for item in items:
            node = item.get('node') or item
            link = node.get('url')
            
            try: price_val = float(node['price']['amount']['value'])
            except: price_val = 0
            
            loc_city = node.get('location', {}).get('city', {}).get('name', 'Nieznane')
            loc_region = node.get('location', {}).get('region', {}).get('name', 'Nieznane')
            
            features_list = node.get('features', []) 
            equip_count = len(features_list)
            equip_str = ", ".join(features_list)
            
            images_count = len(node.get('images', []))
            
            seller_type_raw = node.get('seller', {}).get('type', '')
            seller_type = "Dealer" if seller_type_raw == 'business' else "Prywatny"

            c = {'Rok': 0, 'Przebieg': 0, 'Pojemnosc': 0, 'Moc': 0, 'Paliwo': '', 'Generacja': ''}
            params = node.get('parameters', [])
            for p in params:
                k = p.get('key'); v = p.get('value'); dv = p.get('displayValue')
                if k == 'year': c['Rok'] = v
                elif k == 'mileage': c['Przebieg'] = v
                elif k == 'engine_capacity': c['Pojemnosc'] = v
                elif k == 'engine_power': c['Moc'] = v
                elif k == 'fuel_type': c['Paliwo'] = dv
                elif k == 'generation': c['Generacja'] = dv

            db_data = {
                'url': link, 
                'platforma': 'otomoto',
                'tytul': f"{marka} {model_nazwa} {c['Generacja']}".strip(),
                'cena': int(price_val),
                'marka': marka, 
                'model': model_nazwa,
                'generacja': c['Generacja'],
                'rocznik': clean_int(c['Rok']), 
                'przebieg': clean_int(c['Przebieg']),
                'paliwo': c['Paliwo'], 
                'pojemnosc': clean_int(c['Pojemnosc']),
                'moc': clean_int(c['Moc']),
                'miasto': loc_city,
                'wojewodztwo': loc_region,
                'typ_sprzedawcy': seller_type,
                'liczba_zdjec': images_count,
                'liczba_opcji': equip_count,
                'wyposazenie': equip_str,
                'opis': '' 
            }
            
            status = db.upsert_oferta(db_data)
            
            if status == "INSERT" or status == "UPDATE_PRICE":
                driver.get(link)
                try: WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except: pass
                
                db_data['opis'] = parse_html_description_only(driver)
                db.upsert_oferta(db_data) 
                
                if status == "INSERT":
                    stats.add_new()
                    log.info(f"New: {db_data['cena']} PLN")
                else:
                    stats.add_price_change()
                    log.info(f"Price update: {db_data['cena']} PLN")
            
            elif status == "SEEN":
                stats.add_seen()
                # log.info(f"Seen: {db_data['cena']} PLN") # Opcjonalnie, jesli chcesz widziec kazde
            
            elif status == "ERROR":
                stats.add_error()
                log.error(f"Save error: {link}")
            
            stats.add_processed()
            
        page += 1