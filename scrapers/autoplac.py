from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import re
import json
from utils.cleaning import clean_int
from utils.config import ROK_OD, TYLKO_NIEUSZKODZONE
from utils.network import retry

@retry(max_retries=3, delay=2)
def extract_links(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = set()
    found_any = False
    
    for a in soup.find_all('a', href=True):
        if '/oferta/' in a['href']:
            found_any = True
            full = a['href'] if a['href'].startswith('http') else f"https://autoplac.pl{a['href']}"
            links.add(full)
            
    if not found_any:
        # Jesli pusta lista - byc moze blad ladowania (retry sprobuje ponownie)
        # Ale w Autoplac moze to tez oznaczac koniec stron.
        # Mozna tu rzucic wyjatek jesli jestes pewien ze strona powinna miec wyniki
        pass 
        
    return list(links)

@retry(max_retries=2, delay=1)
def parse_details(driver, url, marka, model):
    details = {
        'Marka pojazdu': marka.capitalize(), 
        'Model pojazdu': model.replace('-', ' ').title(),
        'Link': url, 'Cena': None, 'Data_Aktualizacji': '', 'Rok produkcji': None
    }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 1. Cena (JSON + Regex)
    found_price = None
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            d = json.loads(script.string)
            if isinstance(d, list): d = d[0]
            if 'offers' in d and 'price' in d['offers']:
                found_price = int(float(d['offers']['price']))
        except: pass
        
    if not found_price:
        txt = soup.get_text()
        matches = re.findall(r'(\d[\d\s]*)\s*(?:zł|PLN)', txt)
        nums = [int(re.sub(r'\D', '', m)) for m in matches if re.sub(r'\D', '', m)]
        valid = [n for n in nums if 1000 < n < 5000000]
        if valid: found_price = max(valid)
    
    details['Cena'] = found_price

    # 2. Data
    m_date = re.search(r'aktualizacja.*?(\d{4}-\d{2}-\d{2})', soup.get_text(), re.IGNORECASE)
    if m_date: details['Data_Aktualizacji'] = m_date.group(1)

    # 3. Parametry
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

    return details

def run_autoplac_scraper(driver, db, marka, model_slug, model_nazwa):
    damage_param = "&damagedVehicles=false" if TYLKO_NIEUSZKODZONE else ""
    url = f"https://autoplac.pl/oferty/samochody-osobowe/{marka}/{model_slug}?yearFrom={ROK_OD}{damage_param}"
    
    print(f"Rozpoczynam Autoplac: {marka} {model_nazwa}")
    page = 1
    
    while True:
        print(f"Strona {page}...")
        
        # Inteligentne czekanie na zaladowanie listy
        try:
            driver.get(f"{url}&p={page}")
            # Czekamy max 10s na jakikolwiek link oferty, zeby miec pewnosc ze strona sie zaladowala
            # (Chyba ze strona jest pusta, wtedy timeout pojdzie, ale extract_links obsluzy)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/oferta/']"))
            )
        except TimeoutException:
            # Moze nie byc ofert, idziemy dalej do extract_links zeby to potwierdzic
            pass
            
        links = extract_links(driver)
        if not links:
            print("Brak ofert na stronie. Koniec.")
            break
            
        for link in links:
            driver.get(link)
            # Czekamy na body, zeby miec pewnosc ze detale sie zaladowaly
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except: pass
            
            d = parse_details(driver, link, marka, model_nazwa)
            if not d: continue
            
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
                'nr_rejestracyjny': d.get('Ma numer rejestracyjny')
            }
            
            status = db.upsert_oferta(db_data)
            print(f"  {db_data['cena']} PLN -> {status}")
            
        page += 1