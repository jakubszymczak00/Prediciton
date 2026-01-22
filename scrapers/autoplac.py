from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import re
import json
from utils.cleaning import clean_int
from utils.mapper import get_generation_by_year
from utils.config import TYLKO_NIEUSZKODZONE
try:
    from utils.config import ROK_OD_DOSTAWCZE
except ImportError:
    ROK_OD_DOSTAWCZE = 2012

from utils.network import retry
from utils.logger import log

def close_cookies(driver):
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            txt = btn.text.lower()
            if "akceptuję" in txt or "zgadzam" in txt or "przejdź" in txt:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return
    except: pass

@retry(max_retries=3, delay=2)
def extract_links(driver, szukana_marka):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = set()
    # Uproszczenie: szukamy po prostu linków ofertowych, filtr marki zrobimy później
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/oferta/' in href:
            full_url = href if href.startswith('http') else f"https://autoplac.pl{href}"
            links.add(full_url)
    return list(links)

def parse_brand_model_from_url(url):
    try:
        parts = url.split('/oferta/')
        if len(parts) > 1:
            path = parts[1]
            segments = path.split('/')
            if len(segments) >= 2:
                marka = segments[0].replace('-', ' ').title()
                model = segments[1].replace('-', ' ').title()
                return marka, model
    except: pass
    return None, None

@retry(max_retries=2, delay=1)
def parse_details(driver, url):
    details = {
        'Cena': None, 'Data_Aktualizacji': '', 'Rok produkcji': None,
        'Miasto': '', 'Wojewodztwo': '', 'Typ_Sprzedawcy': 'Prywatny', 
        'Liczba_Zdjec': 0, 'Liczba_Opcji': 0, 'Wyposazenie': '', 'Opis': '',
        'Tytul_H1': '', 'wersja': '', 'generacja': '', 'naped': ''
    }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    h1 = soup.find('h1')
    if h1: details['Tytul_H1'] = h1.get_text(strip=True)

    # 1. PARSOWANIE JSON-LD
    found_price = None
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            d = json.loads(script.string)
            if isinstance(d, list): d = d[0]
            
            if 'offers' in d and 'price' in d['offers']:
                found_price = int(float(d['offers']['price']))

            if 'driveWheelConfiguration' in d:
                drive = d['driveWheelConfiguration'].lower()
                if "przedni" in drive or "front" in drive: details['naped'] = "Na przednie koła"
                elif "tyln" in drive or "rear" in drive: details['naped'] = "Na tylne koła"
                elif "4x4" in drive: details['naped'] = "4x4"
                else: details['naped'] = d['driveWheelConfiguration']
            
            if 'vehicleTransmission' in d and 'gearbox' not in d['vehicleTransmission'].lower():
                details['skrzynia'] = d['vehicleTransmission']
        except: pass
        
    if not found_price:
        txt = soup.get_text()
        matches = re.findall(r'(\d[\d\s]*)\s*(?:zł|PLN)', txt)
        nums = [int(re.sub(r'\D', '', m)) for m in matches if re.sub(r'\D', '', m)]
        valid = [n for n in nums if 1000 < n < 5000000] # Cena między 1000 a 5mln
        if valid: found_price = max(valid)
        
    details['Cena'] = found_price
    m_date = re.search(r'aktualizacja.*?(\d{4}-\d{2}-\d{2})', soup.get_text(), re.IGNORECASE)
    if m_date: details['Data_Aktualizacji'] = m_date.group(1)

    # 2. PARSOWANIE HTML (Parametry)
    params = {}
    for item in soup.find_all(['li', 'div', 'p']):
        txt = item.get_text(separator="|", strip=True)
        if "|" in txt:
            parts = txt.split("|")
            if len(parts) >= 2:
                key = parts[0].replace(":", "").strip().lower()
                val = parts[1].strip()
                if key and val: params[key] = val

    map_db = {
        'generacja': 'generacja', 'wersja': 'wersja',
        'rok produkcji': 'Rok produkcji', 'przebieg': 'Przebieg',
        'rodzaj paliwa': 'Rodzaj paliwa', 'pojemność silnika': 'Pojemność skokowa', 'moc': 'Moc',
        'nadwozie': 'Typ nadwozia', 'kolor': 'Rodzaj koloru', 'skrzynia biegów': 'Skrzynia biegów',
        'typ napędu': 'naped', 'kraj pochodzenia': 'Kraj pochodzenia', 'numer rejestracyjny': 'Ma numer rejestracyjny'
    }
    
    for k_site, k_db in map_db.items():
        if k_site in params and not details.get(k_db):
            details[k_db] = params[k_site]

    if 'Zarejestrowany w Polsce' not in details and details.get('Ma numer rejestracyjny'):
        details['Zarejestrowany w Polsce'] = 'Tak'

    # --- LOKALIZACJA ---
    city_node = soup.find(class_=re.compile("location__main"))
    region_node = soup.find(class_=re.compile("location__secondary"))

    if city_node: details['Miasto'] = city_node.get_text(strip=True)
    if region_node: details['Wojewodztwo'] = region_node.get_text(strip=True)

    if not details['Miasto']:
        try:
            loc_node = soup.find(class_=re.compile("seller-location__address"))
            if loc_node:
                raw_loc = loc_node.get_text(strip=True)
                city_match = re.match(r"([^\d]+)", raw_loc)
                if city_match: details['Miasto'] = city_match.group(1).strip().replace(',', '')
        except: pass

    if "firma" in soup.get_text().lower() or "dealer" in soup.get_text().lower(): 
        details['Typ_Sprzedawcy'] = "Dealer"

    # --- ZDJĘCIA ---
    img_count = 0
    try:
        page_text = soup.get_text()
        counter_match = re.search(r'1\s*/\s*(\d{1,3})', page_text)
        if counter_match: img_count = int(counter_match.group(1))
    except: pass

    if img_count == 0:
        slider = soup.find(class_=re.compile("slider|gallery"))
        if slider:
            slides = slider.find_all(recursive=False)
            if len(slides) > 1: img_count = len(slides)

    if img_count == 0:
        imgs = soup.find_all('img')
        real_imgs = [i for i in imgs if int(i.get('width', 0) or 0) > 300]
        img_count = len(real_imgs)
    
    details['Liczba_Zdjec'] = img_count

    # --- GENERACJA (Breadcrumbs) ---
    if not details.get('generacja'):
        try:
            url_marka, url_model = parse_brand_model_from_url(url)
            if url_marka and url_model:
                curr_marka = url_marka.lower().replace(" ", "-")
                curr_model = url_model.lower().replace(" ", "-")
                found_gen = None
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/oferty/' in href and curr_marka in href and curr_model in href:
                        parts = href.split('/')
                        if len(parts) >= 6:
                            candidate = parts[-1].split('?')[0]
                            if 0 < len(candidate) < 15 and '=' not in candidate:
                                found_gen = candidate.upper()
                                break
                if found_gen: details['generacja'] = found_gen
        except: pass

    return details

def run_autoplac_scraper(driver, db, stats, marka, model_slug, model_nazwa, kategoria_url="samochody-osobowe", rok_od=None):
    if rok_od is None: rok_od = ROK_OD_DOSTAWCZE
    damage_param = "&damagedVehicles=false" if TYLKO_NIEUSZKODZONE else ""
    url = f"https://autoplac.pl/oferty/{kategoria_url}/{marka}/{model_slug}?yearFrom={rok_od}{damage_param}&order=1"
    
    log.info(f"Autoplac start [{kategoria_url}]: {marka} {model_nazwa}")
    page = 1
    db_kategoria = "osobowe" if "osobowe" in kategoria_url else "dostawcze"
    
    while True:
        log.info(f"Autoplac page {page}...")
        try:
            full_url = f"{url}&p={page}"
            driver.get(full_url)
            close_cookies(driver)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            log.warning("Autoplac timeout.")
            break
            
        links = extract_links(driver, marka)
        if not links:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            links = extract_links(driver, marka)
            if not links: break
        
        log.info(f"Znaleziono {len(links)} pasujących ofert na stronie {page}.")
            
        for link in links:
            driver.get(link)
            try: WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except: pass
            
            d = parse_details(driver, link)
            url_marka, url_model = parse_brand_model_from_url(link)
            
            # --- DEBUGOWANIE BŁĘDÓW ---
            if not d.get('Cena'): 
                log.warning(f"❌ POMINIĘTO (Brak ceny): {link}")
                stats.add_error()
                continue
            
            # Weryfikacja marki w URL (zabezpieczenie przed śmieciami)
            marka_slug_safe = marka.lower().split()[0]
            if marka_slug_safe not in link.lower():
                 log.warning(f"❌ POMINIĘTO (Inna marka): {link}")
                 continue

            final_marka = url_marka if url_marka else (d.get('Marka pojazdu') or marka.capitalize())
            final_model = url_model if url_model else (d.get('Model pojazdu') or model_nazwa)
            tytul = d.get('Tytul_H1') or f"{final_marka} {final_model}"

            final_gen = d.get('generacja')
            final_rok = clean_int(d.get('Rok produkcji'))
            
            if not final_gen and final_rok:
                mapped_gen = get_generation_by_year(final_marka, final_model, final_rok)
                if mapped_gen:
                    final_gen = mapped_gen

            db_data = {
                'url': link, 'platforma': 'autoplac', 'kategoria': db_kategoria,
                'tytul': tytul.strip(),
                'cena': d.get('Cena'), 'zrodlo_aktualizacja': d.get('Data_Aktualizacji'),
                'marka': final_marka, 'model': final_model,
                'generacja': final_gen,
                'wersja': d.get('wersja'),
                'rocznik': final_rok,
                'przebieg': clean_int(d.get('Przebieg')),
                'paliwo': d.get('Rodzaj paliwa'),
                'pojemnosc': clean_int(d.get('Pojemność skokowa')),
                'moc': clean_int(d.get('Moc')),
                'nadwozie': d.get('Typ nadwozia'), 'kolor': d.get('Rodzaj koloru'),
                'skrzynia': d.get('Skrzynia biegów'), 'naped': d.get('naped'),
                'kraj': d.get('Kraj pochodzenia'),
                'zarejestrowany': d.get('Zarejestrowany w Polsce'),
                'nr_rejestracyjny': d.get('Ma numer rejestracyjny'),
                'miasto': d.get('Miasto'), 'wojewodztwo': d.get('Wojewodztwo'),
                'typ_sprzedawcy': d.get('Typ_Sprzedawcy'),
                'liczba_zdjec': d.get('Liczba_Zdjec'),
                'liczba_opcji': d.get('Liczba_Opcji'),
                'wyposazenie': d.get('Wyposazenie'),
                'opis': d.get('Opis')
            }
            
            status = db.upsert_oferta(db_data)
            
            if status == "INSERT":
                stats.add_new()
                log.info(f"✅ New: {db_data['cena']} PLN | {db_data['miasto']} | {db_data['generacja']}")
            elif status != "SEEN":
                stats.add_price_change()
                log.info(f"🔄 Update: {db_data['cena']} PLN")
            elif status == "SEEN":
                stats.add_seen() 
            
            stats.add_processed()
        page += 1