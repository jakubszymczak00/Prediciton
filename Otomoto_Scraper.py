import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import os
import re

# --- IMPORT BAZY DANYCH ---
from db_manager import BazaDanych

# --- KONFIGURACJA ---
ROK_OD = 2017
TYLKO_NIEUSZKODZONE = True

# --- BAZA MAREK (Twoja pełna lista) ---
SAMOCHODY = {
    "1": {
        "marka": "bmw", "nazwa": "BMW",
        "modele": {
            "1": {"nazwa": "Seria 1", "slug": "seria-1"},
            "2": {"nazwa": "Seria 3", "slug": "seria-3"},
            "3": {"nazwa": "Seria 5", "slug": "seria-5"},
            "4": {"nazwa": "Seria 7", "slug": "seria-7"},
            "5": {"nazwa": "X1", "slug": "x1"},
            "6": {"nazwa": "X3", "slug": "x3"},
            "7": {"nazwa": "X5", "slug": "x5"},
            "8": {"nazwa": "X6", "slug": "x6"}
        }
    },
    "2": {
        "marka": "audi", "nazwa": "Audi",
        "modele": {
            "1": {"nazwa": "A3", "slug": "a3-3-drzwiowe--a3-allstreet--a3-cabrio--a3-limousine--a3-sportback"},
            "2": {"nazwa": "A4", "slug": "a4-allroad--a4-avant--a4-cabrio--a4-limousine"},
            "3": {"nazwa": "A5", "slug": "a5-avant--a5-cabrio--a5-coupe--a5-limousine--a5-sportback"},
            "4": {"nazwa": "A6", "slug": "a6-allroad--a6-avant--a6-avant-e-tron--a6-e-tron--a6-limousine"},
            "5": {"nazwa": "A7", "slug": "a7"},
            "6": {"nazwa": "A8", "slug": "a8"},
            "7": {"nazwa": "Q2", "slug": "q2"},
            "8": {"nazwa": "Q3", "slug": "q3--q3-sportback"},
            "9": {"nazwa": "Q5", "slug": "q5--q5-sportback"},
            "10": {"nazwa": "Q7", "slug": "q7"},
            "11": {"nazwa": "Q8", "slug": "q8--q8-e-tron--q8-sportback-e-tron"}
        }
    },
        "3": {
        "marka": "mercedes-benz", "nazwa": "Mercedes-Benz",
        "modele": {
            "1": {"nazwa": "Klasa A", "slug": "a-klasa"},
            "2": {"nazwa": "Klasa C", "slug": "klasa-c"},
            "3": {"nazwa": "Klasa E", "slug": "klasa-e"},
            "4": {"nazwa": "Klasa S", "slug": "klasa-s"},
            "5": {"nazwa": "CLA", "slug": "cla"},
            "6": {"nazwa": "GLA", "slug": "gla"},
            "7": {"nazwa": "GLC", "slug": "glc"},
            "8": {"nazwa": "GLE", "slug": "gle"}
        }
    },
    "4": {
        "marka": "volkswagen", "nazwa": "Volkswagen",
        "modele": {
            "1": {"nazwa": "Golf", "slug": "golf"},
            "2": {"nazwa": "Passat", "slug": "passat"},
            "3": {"nazwa": "Polo", "slug": "polo"},
            "4": {"nazwa": "Tiguan", "slug": "tiguan"},
            "5": {"nazwa": "Touran", "slug": "touran"},
            "6": {"nazwa": "Arteon", "slug": "arteon"},
            "7": {"nazwa": "Touareg", "slug": "touareg"}
        }
    },
    "5": {
        "marka": "opel", "nazwa": "Opel",
        "modele": {
            "1": {"nazwa": "Astra", "slug": "astra"},
            "2": {"nazwa": "Insignia", "slug": "insignia"},
            "3": {"nazwa": "Corsa", "slug": "corsa"},
            "4": {"nazwa": "Mokka", "slug": "mokka"},
            "5": {"nazwa": "Zafira", "slug": "zafira"}
        }
    },
    "6": {
        "marka": "toyota", "nazwa": "Toyota",
        "modele": {
            "1": {"nazwa": "Corolla", "slug": "corolla"},
            "2": {"nazwa": "Yaris", "slug": "yaris"},
            "3": {"nazwa": "RAV4", "slug": "rav4"},
            "4": {"nazwa": "C-HR", "slug": "c-hr"},
            "5": {"nazwa": "Camry", "slug": "camry"},
            "6": {"nazwa": "Avensis", "slug": "avensis"}
        }
    },
    "7": {
        "marka": "skoda", "nazwa": "Skoda",
        "modele": {
            "1": {"nazwa": "Octavia", "slug": "octavia"},
            "2": {"nazwa": "Superb", "slug": "superb"},
            "3": {"nazwa": "Fabia", "slug": "fabia"},
            "4": {"nazwa": "Kodiaq", "slug": "kodiaq"},
            "5": {"nazwa": "Karoq", "slug": "karoq"},
            "6": {"nazwa": "Rapid", "slug": "rapid"}
        }
    },
    "8": {
        "marka": "seat", "nazwa": "Seat",
        "modele": {
            "1": {"nazwa": "Leon", "slug": "leon"},
            "2": {"nazwa": "Ibiza", "slug": "ibiza"},
            "3": {"nazwa": "Ateca", "slug": "ateca"},
            "4": {"nazwa": "Arona", "slug": "arona"}
        }
    },
    "9": {
        "marka": "ford", "nazwa": "Ford",
        "modele": {
            "1": {"nazwa": "Focus", "slug": "focus"},
            "2": {"nazwa": "Mondeo", "slug": "mondeo"},
            "3": {"nazwa": "Fiesta", "slug": "fiesta"},
            "4": {"nazwa": "Kuga", "slug": "kuga"},
            "5": {"nazwa": "S-Max", "slug": "s-max"}
        }
    },
    "10": {
        "marka": "kia", "nazwa": "Kia",
        "modele": {
            "1": {"nazwa": "Sportage", "slug": "sportage"},
            "2": {"nazwa": "Ceed", "slug": "ceed"},
            "3": {"nazwa": "Rio", "slug": "rio"},
            "4": {"nazwa": "Stonic", "slug": "stonic"},
            "5": {"nazwa": "Optima", "slug": "optima"}
        }
    },
    "11": {
        "marka": "hyundai", "nazwa": "Hyundai",
        "modele": {
            "1": {"nazwa": "Tucson", "slug": "tucson"},
            "2": {"nazwa": "i30", "slug": "i30"},
            "3": {"nazwa": "i20", "slug": "i20"},
            "4": {"nazwa": "Kona", "slug": "kona"},
            "5": {"nazwa": "Santa Fe", "slug": "santa-fe"}
        }
    },
    "12": {
        "marka": "mazda", "nazwa": "Mazda",
        "modele": {
            "1": {"nazwa": "6", "slug": "6"},
            "2": {"nazwa": "3", "slug": "3"},
            "3": {"nazwa": "CX-5", "slug": "cx-5"},
            "4": {"nazwa": "CX-3", "slug": "cx-3"}
        }
    },
    "13": {
        "marka": "honda", "nazwa": "Honda",
        "modele": {
            "1": {"nazwa": "Civic", "slug": "civic"},
            "2": {"nazwa": "CR-V", "slug": "cr-v"},
            "3": {"nazwa": "HR-V", "slug": "hr-v"},
            "4": {"nazwa": "Accord", "slug": "accord"}
        }
    },
    "14": {
        "marka": "volvo", "nazwa": "Volvo",
        "modele": {
            "1": {"nazwa": "XC60", "slug": "xc60"},
            "2": {"nazwa": "XC90", "slug": "xc90"},
            "3": {"nazwa": "V60", "slug": "v60"},
            "4": {"nazwa": "S90", "slug": "s90"},
            "5": {"nazwa": "S60", "slug": "s60"}
        }
    },
    "15": {
        "marka": "peugeot", "nazwa": "Peugeot",
        "modele": {
            "1": {"nazwa": "308", "slug": "308"},
            "2": {"nazwa": "3008", "slug": "3008"},
            "3": {"nazwa": "508", "slug": "508"},
            "4": {"nazwa": "208", "slug": "208"},
            "5": {"nazwa": "5008", "slug": "5008"}
        }
    },
    "16": {
        "marka": "renault", "nazwa": "Renault",
        "modele": {
            "1": {"nazwa": "Clio", "slug": "clio"},
            "2": {"nazwa": "Megane", "slug": "megane"},
            "3": {"nazwa": "Talisman", "slug": "talisman"},
            "4": {"nazwa": "Captur", "slug": "captur"},
            "5": {"nazwa": "Kadjar", "slug": "kadjar"}
        }
    }
}

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_menu_choice():
    clear_console()
    print("==========================================")
    print(f" 🟠 OTOMOTO SCRAPER -> DB (JSON MODE) 🟠")
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
    options.page_load_strategy = 'eager'
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    # FIX: Twoja wersja Chrome 142
    driver = uc.Chrome(options=options, version_main=142)
    driver.maximize_window()
    return driver

# --- CZĘŚĆ 1: LISTA (JSON - Twoja sprawdzona metoda) ---
def extract_list_data_from_json(driver):
    script = """try { const json = JSON.parse(document.getElementById('__NEXT_DATA__').innerText); return json.props.pageProps.urqlState; } catch(e) { return null; }"""
    cars_basic = []
    try:
        urql_cache = driver.execute_script(script)
        if not urql_cache: return []
        
        for key, value in urql_cache.items():
            try:
                data = json.loads(value['data'])
                list_nodes = []
                # Otomoto ma dwa formaty JSONa, ten kod obsługuje oba
                if 'advertSearch' in data and 'edges' in data['advertSearch']: list_nodes = data['advertSearch']['edges']
                elif 'search' in data and 'results' in data['search']: list_nodes = data['search']['results']
                
                if list_nodes:
                    for item in list_nodes:
                        node = item.get('node') or item
                        if not node.get('price'): continue
                        
                        car = {
                            'Marka pojazdu': '', 'Model pojazdu': '',
                            'Cena': float(node['price']['amount']['value']),
                            'Przebieg': '', 'Rok produkcji': '', 'Rodzaj paliwa': '', 
                            'Pojemność skokowa': '', 'Moc': '', 
                            'Link': node.get('url')
                        }
                        
                        params = node.get('parameters', [])
                        for p in params:
                            k = p.get('key'); v = p.get('value')
                            if k == 'make': car['Marka pojazdu'] = p.get('displayValue')
                            if k == 'model': car['Model pojazdu'] = p.get('displayValue')
                            if k == 'year': car['Rok produkcji'] = v
                            if k == 'mileage': car['Przebieg'] = v
                            if k == 'engine_capacity': car['Pojemność skokowa'] = v
                            if k == 'engine_power': car['Moc'] = v
                            if k == 'fuel_type': car['Rodzaj paliwa'] = p.get('displayValue')

                        cars_basic.append(car)
                    if cars_basic: break
            except: continue
    except: pass
    return cars_basic

# --- CZĘŚĆ 2: DETALE (HTML - Twoja sprawdzona metoda) ---
def parse_html_details(html_content, url):
    details = {
        'Wersja': '', 'Generacja': '', 'Typ nadwozia': '', 
        'Rodzaj koloru': '', 'Skrzynia biegów': '', 'Napęd': '',
        'Kraj pochodzenia': '', 'Zarejestrowany w Polsce': 'Nie', 'Ma numer rejestracyjny': '',
        'Data_Aktualizacji': ''
    }
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        all_items = soup.find_all(['li', 'div'])
        page_params = {}
        
        for item in all_items:
            # Twoja metoda separatora "|" jest najlepsza dla Otomoto
            text = item.get_text(separator="|", strip=True)
            if "|" in text:
                parts = text.split("|")
                if len(parts) >= 2:
                    label = parts[0].replace(":", "").strip()
                    val = parts[1].strip()
                    if 2 < len(label) < 40 and 0 < len(val) < 80:
                        if label not in page_params:
                            page_params[label] = val

        mapping = {
            'Wersja': 'Wersja', 'Generacja': 'Generacja', 'Typ nadwozia': 'Typ nadwozia',
            'Rodzaj koloru': 'Rodzaj koloru', 'Skrzynia biegów': 'Skrzynia biegów',
            'Napęd': 'Napęd', 'Kraj pochodzenia': 'Kraj pochodzenia',
            'Ma numer rejestracyjny': 'Ma numer rejestracyjny'
        }

        for my_key, oto_key in mapping.items():
            if oto_key in page_params:
                details[my_key] = page_params[oto_key]
            
            # Backupy
            if my_key == 'Rodzaj koloru' and not details[my_key]: details[my_key] = page_params.get('Kolor', '')
            if my_key == 'Skrzynia biegów' and not details[my_key]: details[my_key] = page_params.get('Skrzynia', '')

        # Checkboxy w tekście
        full_text = soup.get_text()
        if "Zarejestrowany w PolsceTak" in full_text.replace("\n", "").replace(" ", ""):
             details['Zarejestrowany w Polsce'] = "Tak"

        # Data aktualizacji (Otomoto - próba z JSON-LD lub tekstu)
        try:
            date_match = re.search(r'Dodane dnia\s*(\d{1,2}\s\w+\s\d{4})', full_text, re.IGNORECASE)
            if date_match:
                details['Data_Aktualizacji'] = date_match.group(1)
        except: pass
        
    except Exception as e:
        pass
    
    return details

# --- FUNKCJA CZYSZCZĄCA (Żeby nie sklejało liczb np. 199820) ---
def clean_int(val):
    if not val: return 0
    try:
        val_str = str(val).replace(" ", "").replace("\xa0", "")
        # Bierzemy PIERWSZĄ liczbę z ciągu (np. z "1998 cm3" bierze "1998")
        match = re.search(r'(\d+)', val_str)
        if match:
            liczba = int(match.group(1))
            # Bezpiecznik: jeśli liczba jest kosmiczna (np. > 5mln), to błąd
            if liczba > 5000000: return 0 
            return liczba
        return 0
    except: return 0

def main():
    # Inicjalizacja Bazy
    db = BazaDanych("baza_pojazdow.db")

    marka_slug, model_slug = get_menu_choice()
    if not marka_slug: return

    # URL ZGODNY Z OTOMOTO (slugi z bazy muszą być poprawne, np. 'klasa-a')
    base_url = f"https://www.otomoto.pl/osobowe/{marka_slug}/{model_slug}/od-{ROK_OD}"
    if TYLKO_NIEUSZKODZONE:
        base_url += "?search%5Bfilter_enum_damaged%5D=0"
    
    print(f"\n🚀 START! Cel: {marka_slug.upper()} {model_slug.upper()} (Od {ROK_OD})")
    print(f"🔗 URL: {base_url}")
    
    driver = init_driver()
    page = 1
    total_processed = 0

    try:
        while True:
            # Paginacja Otomoto używa '&page=' lub '?page='
            separator = "&" if "?" in base_url else "?"
            current_url = f"{base_url}{separator}page={page}"
            
            print(f"\n📄 Strona {page}...", end=" ")
            driver.get(current_url)
            time.sleep(2)
            
            # 1. Pobieramy listę z JSONa (Szybko i dokładnie)
            basic_cars = extract_list_data_from_json(driver)
            
            if not basic_cars:
                print("🛑 Koniec wyników.")
                break
            
            print(f"Znaleziono {len(basic_cars)} ofert. Przetwarzanie...")
            
            for i, car in enumerate(basic_cars):
                link = car['Link']
                print(f"   [{i+1}/{len(basic_cars)}] ", end="")
                
                # Sprawdzamy cenę w bazie przed wejściem
                stara_cena = db.sprawdz_cene_przed_zmiana(link)
                
                # Wchodzimy w ofertę po szczegóły
                driver.get(link)
                # Scroll żeby załadować HTML
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.8)
                
                # 2. Parsujemy szczegóły z HTML (Kolor, Skrzynia, itp.)
                details = parse_html_details(driver.page_source, link)
                
                # Łączymy dane z listy (car) i szczegóły (details)
                full_car = {**car, **details}
                
                # --- MAPOWANIE DO BAZY DANYCH ---
                oferta_do_bazy = {
                    'url': full_car['Link'],
                    'platforma': 'otomoto',  # WAŻNE: Oznaczamy że to Otomoto
                    'tytul': f"{full_car.get('Marka pojazdu')} {full_car.get('Model pojazdu')} {full_car.get('Generacja', '')}".strip(),
                    'cena': int(full_car['Cena']),
                    'zrodlo_aktualizacja': full_car.get('Data_Aktualizacji', ''),
                    
                    'marka': full_car.get('Marka pojazdu'),
                    'model': full_car.get('Model pojazdu'),
                    'wersja': full_car.get('Wersja'),
                    'generacja': full_car.get('Generacja'),
                    
                    'rocznik': clean_int(full_car.get('Rok produkcji')),
                    'przebieg': clean_int(full_car.get('Przebieg')),
                    'paliwo': full_car.get('Rodzaj paliwa'),
                    'pojemnosc': clean_int(full_car.get('Pojemność skokowa')),
                    'moc': clean_int(full_car.get('Moc')),
                    
                    'nadwozie': full_car.get('Typ nadwozia'),
                    'kolor': full_car.get('Rodzaj koloru'),
                    'skrzynia': full_car.get('Skrzynia biegów'),
                    'naped': full_car.get('Napęd'),
                    'kraj': full_car.get('Kraj pochodzenia'),
                    'zarejestrowany': full_car.get('Zarejestrowany w Polsce'),
                    'nr_rejestracyjny': full_car.get('Ma numer rejestracyjny')
                }
                
                # Zapisujemy do bazy (Upsert)
                db.upsert_oferta(oferta_do_bazy)
                
                # Wyświetlamy status
                cena_teraz = oferta_do_bazy['cena']
                if stara_cena is None:
                    print(f"✅ [NOWE] {cena_teraz} PLN")
                elif stara_cena != cena_teraz:
                    print(f"💰 [ZMIANA] {stara_cena} -> {cena_teraz} PLN")
                else:
                    print(f"🔄 [OK]")
                
                total_processed += 1
            
            print(f"✅ Strona {page} gotowa.")
            page += 1

    except KeyboardInterrupt:
        print("\n🛑 Przerwano.")
    finally:
        try: driver.quit()
        except: pass
        print(f"\n🎉 ZAKOŃCZONO! Przetworzono: {total_processed}")

if __name__ == "__main__":
    main()