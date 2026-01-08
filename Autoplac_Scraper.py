import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import os
import re
import json

from db_manager import BazaDanych

# --- KONFIGURACJA ---
ROK_OD = 2017
TYLKO_NIEUSZKODZONE = True

# --- BAZA MAREK ---
SAMOCHODY = {
    "1": {"marka": "bmw", "nazwa": "BMW", "modele": {
            "1": {"nazwa": "Seria 1", "slug": "seria-1"},
            "2": {"nazwa": "Seria 2", "slug": "seria-2"},
            "3": {"nazwa": "Seria 3", "slug": "seria-3"},
            "4": {"nazwa": "Seria 4", "slug": "seria-4"},
            "5": {"nazwa": "Seria 5", "slug": "seria-5"},
            "6": {"nazwa": "Seria 6", "slug": "seria-6"},
            "7": {"nazwa": "Seria 7", "slug": "seria-7"},
            "8": {"nazwa": "Seria 8", "slug": "seria-8"},
            "9": {"nazwa": "X1", "slug": "x1"},
            "10": {"nazwa": "X2", "slug": "x2"},
            "11": {"nazwa": "X3", "slug": "x3"},
            "12": {"nazwa": "X4", "slug": "x4"},
            "13": {"nazwa": "X5", "slug": "x5"},
            "14": {"nazwa": "X6", "slug": "x6"},
            "15": {"nazwa": "X7", "slug": "x7"},
    }},
    # ... (Reszta Twoich marek) ...
    "2": {"marka": "audi", "nazwa": "Audi", "modele": {
            "1": {"nazwa": "A3", "slug": "a3"},
            "2": {"nazwa": "A4", "slug": "a4"},
            "3": {"nazwa": "Q5", "slug": "q5"}
    }},
    "3": {"marka": "mercedes-benz", "nazwa": "Mercedes-benz", "modele": {
            "1": {"nazwa": "Klasa A", "slug": "klasa-a"},

    }},
    "4": {"marka": "volkswagen", "nazwa": "Volkswagen", "modele": {
            "1": {"nazwa": "Golf", "slug": "golf"},
            "2": {"nazwa": "Passat", "slug": "passat"},
            "3": {"nazwa": "Tiguan", "slug": "tiguan"}
    }},
    "5": {"marka": "ford", "nazwa": "Ford", "modele": {
            "1": {"nazwa": "Focus", "slug": "focus"},
            "2": {"nazwa": "Mondeo", "slug": "mondeo"},
            "3": {"nazwa": "Kuga", "slug": "kuga"}
    }}
}

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_menu_choice():
    clear_console()
    print("==========================================")
    print(f" 🔵 AUTOPLAC SCRAPER v5.0 (OLD PARSER + DB) 🔵")
    print("==========================================")
    print("Wybierz markę:")
    for k, v in SAMOCHODY.items():
        print(f"[{k}] {v['nazwa']}")
    
    wybor_marka = input("\nTwój wybór (cyfra): ")
    if wybor_marka not in SAMOCHODY: return None, None
    wybrana_marka = SAMOCHODY[wybor_marka]
    
    print(f"\n--- Wybrano: {wybrana_marka['nazwa']} ---")
    print("Wybierz model:")
    for k, v in wybrana_marka['modele'].items():
        print(f"[{k}] {v['nazwa']}")
        
    wybor_model = input("\nTwój wybór (cyfra): ")
    if wybor_model not in wybrana_marka['modele']: return None, None
    wybrany_model = wybrana_marka['modele'][wybor_model]
    
    return wybrana_marka['marka'], wybrany_model['slug']

def init_driver():
    options = uc.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    options.page_load_strategy = 'eager'
    driver = uc.Chrome(options=options, version_main=142)
    driver.maximize_window()
    return driver

def extract_autoplac_list(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cars = []
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if '/oferta/' in href:
            full_link = href if href.startswith('http') else f"https://autoplac.pl{href}"
            cars.append({'Link': full_link})
    unique_cars = []
    seen = set()
    for c in cars:
        if c['Link'] not in seen:
            seen.add(c['Link'])
            unique_cars.append(c)
    return unique_cars

# TO JEST FUNKCJA PARSUJĄCA
def parse_offer_details(driver, url, marka_default, model_default):
    details = {
        'Marka pojazdu': marka_default.capitalize(),
        'Model pojazdu': model_default.replace('-', ' ').title(),
        'Wersja': '', 
        'Generacja': '', 
        'Cena': 0, 
        'Przebieg': '', 
        'Rok produkcji': '',
        'Rodzaj paliwa': '', 
        'Pojemność skokowa': '', 
        'Moc': '', 
        'Typ nadwozia': '',
        'Rodzaj koloru': '',
        'Skrzynia biegów': '',
        'Napęd': '',
        'Kraj pochodzenia': '',
        'Zarejestrowany w Polsce': 'Nie',
        'Ma numer rejestracyjny': '',
        'Data_Aktualizacji': '',
        'Link': url
    }
    
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # --- 1. CENA (Ulepszona o JSON, żeby było pewniej) ---
        found_price = None
        try:
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                if found_price: break
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        price = None
                        if item.get('@type') == 'Offer': price = item.get('price')
                        elif 'offers' in item:
                            offers = item['offers']
                            if isinstance(offers, dict): price = offers.get('price')
                            elif isinstance(offers, list) and offers: price = offers[0].get('price')
                        if price:
                            found_price = int(float(price))
                            break
                except: continue
        except: pass
        
        # Fallback dla ceny (Twoja stara metoda z tekstu)
        if not found_price:
            all_texts = soup.get_text(separator="|").split("|")
            for txt in all_texts:
                clean = txt.replace(" ", "").strip()
                if "zł" in txt and any(char.isdigit() for char in clean):
                     raw_price = clean.replace("zł", "").replace("PLN", "").replace("BRUTTO", "")
                     # Usuwamy wszystko co nie jest cyfrą
                     raw_price = re.sub(r'\D', '', raw_price)
                     if len(raw_price) > 3:
                         found_price = int(raw_price)
                         break
        
        if found_price: details['Cena'] = found_price

        # --- 2. DATA AKTUALIZACJI ---
        try:
            full_text = soup.get_text()
            match_date = re.search(r'aktualizacja.*?(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}|\d{4}-\d{2}-\d{2})', full_text, re.IGNORECASE)
            if match_date: details['Data_Aktualizacji'] = match_date.group(1)
        except: pass

        # --- 3. PARAMETRY (PO STAREMU - separator "|") ---
        # To jest ten kluczowy fragment, który działał dobrze w CSV
        
        # Pobieramy wszystkie parametry (li i divy)
        all_items = soup.find_all(['li', 'div'])
        page_params = {}
        
        for item in all_items:
            # Triki na wyciągnięcie tekstu "Etykieta|Wartość"
            text = item.get_text(separator="|", strip=True)
            if "|" in text:
                parts = text.split("|")
                if len(parts) >= 2:
                    label = parts[0].replace(":", "").strip()
                    val = parts[1].strip()
                    # Filtry żeby nie łapać śmieci
                    if 2 < len(label) < 40 and 0 < len(val) < 80:
                        if label not in page_params:
                            page_params[label] = val

        # Mapowanie Twoich kluczy
        mapping = {
            'generacja': 'Generacja', 
            'rok produkcji': 'Rok produkcji', 
            'przebieg': 'Przebieg',
            'rodzaj paliwa': 'Rodzaj paliwa', 
            'pojemność silnika': 'Pojemność skokowa', 
            'moc': 'Moc',
            'nadwozie': 'Typ nadwozia', 
            'kolor': 'Rodzaj koloru', 
            'skrzynia biegów': 'Skrzynia biegów',
            'typ napędu': 'Napęd', 
            'kraj pochodzenia': 'Kraj pochodzenia', 
            'numer rejestracyjny': 'Ma numer rejestracyjny',
            'wersja': 'Wersja'
        }

        # Iterujemy po mapowaniu i szukamy w znalezionych page_params (case insensitive)
        # Tworzymy słownik lowercase dla łatwiejszego szukania
        params_lower = {k.lower(): v for k, v in page_params.items()}

        for key_in_code, key_in_db in mapping.items():
            if key_in_code in params_lower:
                details[key_in_db] = params_lower[key_in_code]

        # --- 4. DODATKOWE FIXY ---
        if details['Ma numer rejestracyjny']: 
            details['Zarejestrowany w Polsce'] = 'Tak'
        else:
            full_text = soup.get_text().lower()
            if "zarejestrowany" in full_text and "nie zarejestrowany" not in full_text:
                 if "zarejestrowany w polscetak" in full_text.replace("\n", "").replace(" ", ""):
                     details['Zarejestrowany w Polsce'] = "Tak"

    except Exception as e:
        pass
        
    return details

def clean_int(val):
    """Czyści liczby, bierze pierwszą napotkaną, ignoruje resztę"""
    if not val: return 0
    try:
        val_str = str(val).replace(" ", "").replace("\xa0", "")
        match = re.search(r'(\d+)', val_str)
        if match:
            liczba = int(match.group(1))
            if liczba > 5000000: return 0 
            return liczba
        return 0
    except: return 0

def main():
    db = BazaDanych("baza_pojazdow.db")

    marka_slug, model_slug = get_menu_choice()
    if not marka_slug: return

    damage_param = "false" if TYLKO_NIEUSZKODZONE else "true"
    base_url = f"https://autoplac.pl/oferty/samochody-osobowe/{marka_slug}/{model_slug}?yearFrom={ROK_OD}&damagedVehicles={damage_param}"
    
    print(f"\n🚀 START! Cel: {marka_slug.upper()} {model_slug.upper()}")
    driver = init_driver()
    page = 1
    total_processed = 0
    global_seen_links = set()

    try:
        while True:
            current_url = f"{base_url}&p={page}"
            print(f"\n📄 Strona {page} (p={page})...", end=" ")
            driver.get(current_url)
            time.sleep(2.5)
            
            offer_list = extract_autoplac_list(driver)
            new_offers = [o for o in offer_list if o['Link'] not in global_seen_links]
            for o in new_offers: global_seen_links.add(o['Link'])
            
            if not new_offers: print("🛑 Koniec."); break
            
            print(f"Znaleziono {len(new_offers)} ofert. Przetwarzanie...")
            
            for i, item in enumerate(new_offers):
                link = item['Link']
                print(f"   [{i+1}/{len(new_offers)}] ", end="")
                
                stara_cena = db.sprawdz_cene_przed_zmiana(link)
                driver.get(link)
                time.sleep(1)
                
                full_data = parse_offer_details(driver, link, marka_slug, model_slug)
                
                oferta_do_bazy = {
                    'url': full_data['Link'],
                    'platforma': 'autoplac',
                    'tytul': f"{full_data['Marka pojazdu']} {full_data['Model pojazdu']} {full_data['Generacja']}".strip(),
                    'cena': full_data['Cena'],
                    'zrodlo_aktualizacja': full_data['Data_Aktualizacji'],
                    
                    'marka': full_data['Marka pojazdu'],
                    'model': full_data['Model pojazdu'],
                    'wersja': full_data['Wersja'],
                    'generacja': full_data['Generacja'],
                    'rocznik': clean_int(full_data['Rok produkcji']),
                    'przebieg': clean_int(full_data['Przebieg']),
                    'paliwo': full_data['Rodzaj paliwa'],
                    'pojemnosc': clean_int(full_data['Pojemność skokowa']),
                    'moc': clean_int(full_data['Moc']),
                    'nadwozie': full_data['Typ nadwozia'],
                    'kolor': full_data['Rodzaj koloru'],
                    'skrzynia': full_data['Skrzynia biegów'],
                    'naped': full_data['Napęd'],
                    'kraj': full_data['Kraj pochodzenia'],
                    'zarejestrowany': full_data['Zarejestrowany w Polsce'],
                    'nr_rejestracyjny': full_data['Ma numer rejestracyjny']
                }
                
                # DEBUG
                # print(json.dumps(oferta_do_bazy, indent=4, ensure_ascii=False))
                
                db.upsert_oferta(oferta_do_bazy)
                
                cena_teraz = oferta_do_bazy['cena']
                if stara_cena is None:
                    print(f"✅ [NOWE] {cena_teraz} PLN")
                elif stara_cena != cena_teraz:
                    print(f"💰 [ZMIANA] {stara_cena} -> {cena_teraz} PLN")
                else:
                    print(f"🔄 [OK]")
                
                total_processed += 1
            page += 1

    except KeyboardInterrupt: print("\n🛑 Przerwano.")
    finally:
        try: driver.quit()
        except: pass
        print(f"\n🎉 ZAKOŃCZONO! Przetworzono: {total_processed}")

if __name__ == "__main__":
    main()