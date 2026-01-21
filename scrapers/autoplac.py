from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import re
import json
from utils.cleaning import clean_int
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
    """
    Pobiera linki do ofert, filtrując te, które nie pasują do szukanej marki.
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = set()
    
    # Normalizacja marki do szukania w URL (np. 'Mercedes-Benz' -> 'mercedes')
    marka_slug = szukana_marka.lower().split()[0] 
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Musi być to link do oferty
        if '/oferta/' in href:
            full_url = href if href.startswith('http') else f"https://autoplac.pl{href}"
            
            # FILTR BEZPIECZEŃSTWA: Sprawdzamy czy marka (lub jej część) jest w URLu.
            # To eliminuje "Proponowane Volvo" gdy szukamy Iveco.
            if marka_slug in full_url.lower():
                links.add(full_url)
            
    return list(links)

def parse_brand_model_from_url(url):
    """
    Próbuje wyciągnąć markę i model z URL.
    Formaty bywają różne: /oferta/marka/model/.. lub /oferta/marka-model-...
    """
    try:
        # Typowy format: autoplac.pl/oferta/volkswagen/transporter/
        parts = url.split('/oferta/')
        if len(parts) > 1:
            path = parts[1]
            segments = path.split('/')
            
            if len(segments) >= 2:
                # Segment 0 to marka, Segment 1 to model
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
        'Tytul_H1': ''
    }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Tytuł
    h1 = soup.find('h1')
    if h1: details['Tytul_H1'] = h1.get_text(strip=True)

    # Cena
    found_price = None
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            d = json.loads(script.string)
            if isinstance(d, list): d = d[0]
            if 'offers' in d and 'price' in d['offers']:
                found_price = int(float(d['offers']['price']))
                break
        except: pass
        
    if not found_price:
        txt = soup.get_text()
        matches = re.findall(r'(\d[\d\s]*)\s*(?:zł|PLN)', txt)
        nums = [int(re.sub(r'\D', '', m)) for m in matches if re.sub(r'\D', '', m)]
        valid = [n for n in nums if 1000 < n < 5000000]
        if valid: found_price = max(valid)
        
    details['Cena'] = found_price

    # Data
    m_date = re.search(r'aktualizacja.*?(\d{4}-\d{2}-\d{2})', soup.get_text(), re.IGNORECASE)
    if m_date: details['Data_Aktualizacji'] = m_date.group(1)

    # Parametry
    params = {}
    # Szukamy par klucz-wartość w elementach listy i divach
    for item in soup.find_all(['li', 'div', 'p']):
        txt = item.get_text(separator="|", strip=True)
        if "|" in txt:
            parts = txt.split("|")
            if len(parts) >= 2:
                key = parts[0].replace(":", "").strip().lower()
                val = parts[1].strip()
                if key and val: params[key] = val

    map_db = {
        'generacja': 'Generacja', 'rok produkcji': 'Rok produkcji', 'przebieg': 'Przebieg',
        'rodzaj paliwa': 'Rodzaj paliwa', 'pojemność silnika': 'Pojemność skokowa', 'moc': 'Moc',
        'nadwozie': 'Typ nadwozia', 'kolor': 'Rodzaj koloru', 'skrzynia biegów': 'Skrzynia biegów',
        'typ napędu': 'Napęd', 'kraj pochodzenia': 'Kraj pochodzenia', 'numer rejestracyjny': 'Ma numer rejestracyjny'
    }
    
    for k_site, k_db in map_db.items():
        if k_site in params: details[k_db] = params[k_site]

    # Rejestracja
    if 'Zarejestrowany w Polsce' not in details and details.get('Ma numer rejestracyjny'):
        details['Zarejestrowany w Polsce'] = 'Tak'

    # Lokalizacja
    try:
        if 'lokalizacja' in params:
            loc_parts = params['lokalizacja'].split(',')
            details['Miasto'] = loc_parts[0].strip()
            if len(loc_parts) > 1: details['Wojewodztwo'] = loc_parts[1].strip()
    except: pass

    # Sprzedawca
    if "firma" in soup.get_text().lower() or "dealer" in soup.get_text().lower(): 
        details['Typ_Sprzedawcy'] = "Dealer"

    # Wyposażenie
    keywords = ["Klimatyzacja", "Skóra", "Nawigacja", "LED", "Kamera", "Czujniki", "Tempomat", "Automat", "Panorama", "Hak", "Bluetooth", "Winda", "Webasto"]
    found_opts = [k for k in keywords if k in soup.get_text()]
    details['Wyposazenie'] = ", ".join(found_opts)
    details['Liczba_Opcji'] = len(found_opts)

    # Opis
    paragraphs = soup.find_all('p')
    if paragraphs:
        longest_p = max(paragraphs, key=lambda p: len(p.get_text()), default=None)
        if longest_p and len(longest_p.get_text()) > 50:
            details['Opis'] = longest_p.get_text(strip=True)[:5000]

    # Zdjęcia
    imgs = soup.find_all('img') 
    real_imgs = [i for i in imgs if int(i.get('width', 0) or 0) > 300]
    details['Liczba_Zdjec'] = len(real_imgs)

    return details

def run_autoplac_scraper(driver, db, stats, marka, model_slug, model_nazwa, kategoria_url="samochody-osobowe", rok_od=None):
    if rok_od is None: rok_od = ROK_OD_DOSTAWCZE
    
    damage_param = "&damagedVehicles=false" if TYLKO_NIEUSZKODZONE else ""
    
    # URL jest teraz budowany poprawnie z parametru kategoria_url
    url = f"https://autoplac.pl/oferty/{kategoria_url}/{marka}/{model_slug}?yearFrom={rok_od}{damage_param}&order=1"
    
    log.info(f"Autoplac start [{kategoria_url}]: {marka} {model_nazwa}")
    page = 1
    
    # Ustawienie kategorii dla bazy
    db_kategoria = "osobowe" if "osobowe" in kategoria_url else "dostawcze"
    
    while True:
        log.info(f"Autoplac page {page}...")
        try:
            full_url = f"{url}&p={page}"
            driver.get(full_url)
            close_cookies(driver)
            # Czekamy aż pojawi się jakakolwiek oferta lub komunikat o braku
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            log.warning("Autoplac timeout.")
            break
            
        # Pobieramy linki z filtrowaniem marki
        links = extract_links(driver, marka)
        
        if not links:
            # Przewijamy, może leniwe ładowanie
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            links = extract_links(driver, marka)
            
            if not links:
                log.info(f"Brak (więcej) ofert dla {model_nazwa} na stronie {page}.")
                break
            
        log.info(f"Znaleziono {len(links)} pasujących ofert na stronie {page}.")
            
        for link in links:
            driver.get(link)
            try: WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except: pass
            
            # Pobieranie danych
            d = parse_details(driver, link)
            url_marka, url_model = parse_brand_model_from_url(link)
            
            if not d.get('Cena'): 
                stats.add_error()
                continue
            
            # Priorytetyzacja danych:
            final_marka = url_marka if url_marka else (d.get('Marka pojazdu') or marka.capitalize())
            final_model = url_model if url_model else (d.get('Model pojazdu') or model_nazwa)
            tytul = d.get('Tytul_H1') or f"{final_marka} {final_model}"

            db_data = {
                'url': link, 'platforma': 'autoplac', 'kategoria': db_kategoria,
                'tytul': tytul.strip(),
                'cena': d.get('Cena'), 'zrodlo_aktualizacja': d.get('Data_Aktualizacji'),
                'marka': final_marka, 
                'model': final_model,
                'generacja': d.get('Generacja'),
                'rocznik': clean_int(d.get('Rok produkcji')),
                'przebieg': clean_int(d.get('Przebieg')),
                'paliwo': d.get('Rodzaj paliwa'),
                'pojemnosc': clean_int(d.get('Pojemność skokowa')),
                'moc': clean_int(d.get('Moc')),
                'nadwozie': d.get('Typ nadwozia'), 'kolor': d.get('Rodzaj koloru'),
                'skrzynia': d.get('Skrzynia biegów'), 'naped': d.get('Napęd'),
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
                log.info(f"New: {db_data['cena']} PLN | {db_data['marka']} {db_data['model']}")
            elif status == "UPDATE_PRICE":
                stats.add_price_change()
                log.info(f"Price update: {db_data['cena']} PLN")
            elif status == "SEEN":
                stats.add_seen() 
            
            stats.add_processed()
            
        page += 1