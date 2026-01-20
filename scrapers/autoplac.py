from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import time
import re
import json
from utils.cleaning import clean_int
from utils.config import ROK_OD, TYLKO_NIEUSZKODZONE
from utils.network import retry
from utils.logger import log

def close_cookies(driver):
    """Agresywnie zamyka banery cookies/RODO na Autoplac"""
    try:
        # Szukamy przyciskow typu "Akceptuje", "Zgadzam sie" itp.
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            txt = btn.text.lower()
            if "akceptuję" in txt or "zgadzam" in txt or "przejdź" in txt:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    log.info("🍪 Zamknięto baner cookies.")
                    time.sleep(1)
                    return
                except: pass
    except: pass

@retry(max_retries=3, delay=2)
def extract_links(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = set()
    found_any = False
    # Szukamy linkow w kafelkach ofert
    for a in soup.find_all('a', href=True):
        if '/oferta/' in a['href']:
            found_any = True
            full = a['href'] if a['href'].startswith('http') else f"https://autoplac.pl{a['href']}"
            links.add(full)
    return list(links)

@retry(max_retries=2, delay=1)
def parse_details(driver, url, marka, model):
    # Domyslny obiekt, zeby nie wywalalo bledu przy braku danych
    details = {
        'Marka pojazdu': marka.capitalize(), 
        'Model pojazdu': model.replace('-', ' ').title(),
        'Link': url, 'Cena': None, 'Data_Aktualizacji': '', 'Rok produkcji': None,
        'Miasto': '', 'Wojewodztwo': '', 'Typ_Sprzedawcy': 'Prywatny', 
        'Liczba_Zdjec': 0, 'Liczba_Opcji': 0, 'Wyposazenie': '', 'Opis': ''
    }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 1. CENA
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

    # 2. DATA AKTUALIZACJI
    m_date = re.search(r'aktualizacja.*?(\d{4}-\d{2}-\d{2})', soup.get_text(), re.IGNORECASE)
    if m_date: details['Data_Aktualizacji'] = m_date.group(1)

    # 3. PARAMETRY
    params = {}
    for item in soup.find_all(['li', 'div']):
        txt = item.get_text(separator="|", strip=True)
        if "|" in txt:
            parts = txt.split("|")
            if len(parts) >= 2:
                params[parts[0].replace(":", "").strip().lower()] = parts[1].strip()

    map_db = {
        'generacja': 'Generacja', 'rok produkcji': 'Rok produkcji', 'przebieg': 'Przebieg',
        'rodzaj paliwa': 'Rodzaj paliwa', 'pojemność silnika': 'Pojemność skokowa', 'moc': 'Moc',
        'nadwozie': 'Typ nadwozia', 'kolor': 'Rodzaj koloru', 'skrzynia biegów': 'Skrzynia biegów',
        'typ napędu': 'Napęd', 'kraj pochodzenia': 'Kraj pochodzenia', 'numer rejestracyjny': 'Ma numer rejestracyjny'
    }
    for k, v in map_db.items():
        if k in params: details[v] = params[k]

    if 'Zarejestrowany w Polsce' not in details and details.get('Ma numer rejestracyjny'):
        details['Zarejestrowany w Polsce'] = 'Tak'

    # 4. NOWE DANE (DASHBOARD)
    try:
        if 'lokalizacja' in params:
            loc_parts = params['lokalizacja'].split(',')
            details['Miasto'] = loc_parts[0].strip()
            if len(loc_parts) > 1: details['Wojewodztwo'] = loc_parts[1].strip()
    except: pass

    if "Firma" in soup.get_text() or "Dealer" in soup.get_text(): 
        details['Typ_Sprzedawcy'] = "Dealer"

    keywords = ["Klimatyzacja", "Skóra", "Nawigacja", "LED", "Kamera", "Czujniki", "Tempomat", "Automat", "Panorama"]
    found_opts = [k for k in keywords if k in soup.get_text()]
    details['Wyposazenie'] = ", ".join(found_opts)
    details['Liczba_Opcji'] = len(found_opts)

    paragraphs = soup.find_all('p')
    if paragraphs:
        longest_p = max(paragraphs, key=lambda p: len(p.get_text()), default=None)
        if longest_p and len(longest_p.get_text()) > 50:
            details['Opis'] = longest_p.get_text(strip=True)[:5000]

    imgs = soup.find_all('img') 
    real_imgs = [i for i in imgs if int(i.get('width', 0) or 0) > 300]
    details['Liczba_Zdjec'] = len(real_imgs)

    return details

def run_autoplac_scraper(driver, db, stats, marka, model_slug, model_nazwa):
    damage_param = "&damagedVehicles=false" if TYLKO_NIEUSZKODZONE else ""
    # Dodajemy parametr sortowania (np. najnowsze), czasem pomaga na paginacje
    url = f"https://autoplac.pl/oferty/samochody-osobowe/{marka}/{model_slug}?yearFrom={ROK_OD}{damage_param}&order=1"
    
    log.info(f"Autoplac start: {marka} {model_nazwa}")
    page = 1
    
    while True:
        log.info(f"Autoplac strona {page}...")
        try:
            full_url = f"{url}&p={page}"
            driver.get(full_url)
            
            # 1. Zamykamy cookies (TO JEST KLUCZOWE)
            close_cookies(driver)
            
            # 2. Czekamy na cokolwiek (nie tylko linki), zeby nie timeoutowac zbyt szybko
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
        except TimeoutException:
            log.warning("Autoplac wolno dziala, ale probuje czytac dalej...")
            
        links = extract_links(driver)
        if not links:
            # Sprawdzenie czy to nie blad ladowania - proba scrolla
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            links = extract_links(driver)
            
            if not links:
                log.info(f"Brak ofert na stronie {page}. Koniec modelu {model_nazwa}.")
                break
            
        log.info(f"Znaleziono {len(links)} ofert na stronie {page}.")
            
        for link in links:
            # Wchodzimy w oferte
            driver.get(link)
            try: WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except: pass
            
            d = parse_details(driver, link, marka, model_nazwa)
            if not d.get('Cena'): 
                stats.add_error()
                continue
            
            db_data = {
                'url': link, 'platforma': 'autoplac',
                'tytul': f"{d.get('Marka pojazdu')} {d.get('Model pojazdu')}".strip(),
                'cena': d.get('Cena'), 'zrodlo_aktualizacja': d.get('Data_Aktualizacji'),
                'marka': d.get('Marka pojazdu'), 'model': d.get('Model pojazdu'),
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
                log.info(f"➕ [NOWE] {db_data['cena']} PLN")
            elif status == "UPDATE_PRICE":
                stats.add_price_change()
                log.info(f"💰 [ZMIANA] {db_data['cena']} PLN")
            elif status == "SEEN":
                # stats.add_seen() - nie spamujemy logow
                pass
            
            stats.add_processed()
            
        page += 1 # Przechodzimy do nastepnej strony