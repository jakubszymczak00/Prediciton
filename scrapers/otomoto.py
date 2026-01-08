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
from utils.network import retry  # <--- NOWY IMPORT

@retry(max_retries=3, delay=3)  # <--- PONAWIJANIE
def extract_list_json(driver):
    # Pobiera liste aut z JSON. Probuje 3 razy w razie bledu.
    script = """try { const json = JSON.parse(document.getElementById('__NEXT_DATA__').innerText); return json.props.pageProps.urqlState; } catch(e) { return null; }"""
    
    urql_cache = driver.execute_script(script)
    if not urql_cache: 
        raise Exception("Brak danych JSON na stronie") # Rzucamy blad zeby retry zadzialalo
        
    results = []
    for key, value in urql_cache.items():
        try:
            data = json.loads(value['data'])
            if 'advertSearch' in data and 'edges' in data['advertSearch']: 
                results.extend(data['advertSearch']['edges'])
            elif 'search' in data and 'results' in data['search']: 
                results.extend(data['search']['results'])
        except: continue
    
    if not results:
        # Czasami JSON jest pusty bo strona sie nie doladowala
        raise Exception("Pusta lista wynikow w JSON")
        
    return results

@retry(max_retries=2, delay=1) # <--- PONAWIJANIE DETALI
def parse_html_details(driver, url):
    # Pobiera detale. Jesli selenium nie znajdzie elementow, sprobuje ponownie.
    details = {
        'Wersja': '', 'Generacja': '', 'Typ nadwozia': '', 'Rodzaj koloru': '', 
        'Skrzynia biegów': '', 'Napęd': '', 'Kraj pochodzenia': '', 
        'Zarejestrowany w Polsce': 'Nie', 'Ma numer rejestracyjny': '', 'Data_Aktualizacji': ''
    }
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Parametry
    all_items = soup.find_all(['li', 'div'])
    page_params = {}
    for item in all_items:
        text = item.get_text(separator="|", strip=True)
        if "|" in text:
            parts = text.split("|")
            if len(parts) >= 2:
                page_params[parts[0].replace(":", "").strip()] = parts[1].strip()

    mapping = {
        'Wersja': 'Wersja', 'Generacja': 'Generacja', 'Typ nadwozia': 'Typ nadwozia',
        'Rodzaj koloru': 'Rodzaj koloru', 'Skrzynia biegów': 'Skrzynia biegów',
        'Napęd': 'Napęd', 'Kraj pochodzenia': 'Kraj pochodzenia',
        'Ma numer rejestracyjny': 'Ma numer rejestracyjny'
    }
    for k, v in mapping.items():
        if k in page_params: details[v] = page_params[k]

    if "Zarejestrowany w PolsceTak" in soup.get_text().replace("\n", "").replace(" ", ""):
            details['Zarejestrowany w Polsce'] = "Tak"

    try:
        date_match = re.search(r'Dodane dnia\s*(\d{1,2}\s\w+\s\d{4})', soup.get_text(), re.IGNORECASE)
        if date_match: details['Data_Aktualizacji'] = date_match.group(1)
    except: pass
    
    return details

def run_otomoto_scraper(driver, db, marka, model_slug, model_nazwa):
    damage_param = "?search%5Bfilter_enum_damaged%5D=0" if TYLKO_NIEUSZKODZONE else ""
    url = f"https://www.otomoto.pl/osobowe/{marka}/{model_slug}/od-{ROK_OD}{damage_param}"
    
    print(f"Rozpoczynam Otomoto: {marka} {model_nazwa}")
    page = 1
    
    while True:
        separator = "&" if "?" in url else "?"
        print(f"Strona {page}...")
        
        # Prosta obsluga bledu ladowania strony glownej
        try:
            driver.get(f"{url}{separator}page={page}")
            
            # Czekamy max 10 sekund, aż pojawi się element JSON (__NEXT_DATA__)
            # Jak tylko się pojawi, idziemy dalej.
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
        except TimeoutException:
            print("Strona ładowała się zbyt długo (timeout elementu).")
            # Tutaj @retry z poziomu funkcji nadrzędnej i tak by zadziałało,
            # ale możemy też po prostu spróbować przejść dalej, bo extract_list_json też ma retry.
        
        items = extract_list_json(driver)
        if not items:
            print("Brak ofert lub blokada. Koniec.")
            break
            
        for item in items:
            # Obsluga roznych struktur JSON
            node = item.get('node') or item
            link = node.get('url')
            
            # Pobieramy podstawy z JSONa
            try:
                price_val = float(node['price']['amount']['value'])
            except:
                price_val = 0
            
            c = {
                'Marka': '', 'Model': '', 'Cena': price_val,
                'Rok': '', 'Przebieg': '', 'Paliwo': '', 'Pojemnosc': '', 'Moc': ''
            }
            
            params = node.get('parameters', [])
            for p in params:
                k = p.get('key'); v = p.get('value')
                if k == 'make': c['Marka'] = p.get('displayValue')
                if k == 'model': c['Model'] = p.get('displayValue')
                if k == 'year': c['Rok'] = v
                if k == 'mileage': c['Przebieg'] = v
                if k == 'engine_capacity': c['Pojemnosc'] = v
                if k == 'engine_power': c['Moc'] = v
                if k == 'fuel_type': c['Paliwo'] = p.get('displayValue')

            # Detale z HTML
            driver.get(link)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            det = parse_html_details(driver, link)
            if not det: det = {} # Zabezpieczenie jesli retry zwroci None
            
            db_data = {
                'url': link, 'platforma': 'otomoto',
                'tytul': f"{c['Marka']} {c['Model']} {det.get('Generacja', '')}".strip(),
                'cena': int(c['Cena']), 'zrodlo_aktualizacja': det.get('Data_Aktualizacji'),
                'marka': c['Marka'], 'model': c['Model'],
                'wersja': det.get('Wersja'), 'generacja': det.get('Generacja'),
                'rocznik': clean_int(c['Rok']), 'przebieg': clean_int(c['Przebieg']),
                'paliwo': c['Paliwo'], 'pojemnosc': clean_int(c['Pojemnosc']),
                'moc': clean_int(c['Moc']),
                'nadwozie': det.get('Typ nadwozia'), 'kolor': det.get('Rodzaj koloru'),
                'skrzynia': det.get('Skrzynia biegów'), 'naped': det.get('Napęd'),
                'kraj': det.get('Kraj pochodzenia'),
                'zarejestrowany': det.get('Zarejestrowany w Polsce'),
                'nr_rejestracyjny': det.get('Ma numer rejestracyjny')
            }
            
            status = db.upsert_oferta(db_data)
            print(f"  {db_data['cena']} PLN -> {status}")
            
        page += 1