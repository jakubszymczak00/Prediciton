import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import os
import re
import json

# --- KONFIGURACJA ---
# Wpisz tutaj dokładną nazwę pliku CSV, który chcesz naprawić
NAZWA_PLIKU_CSV = "autoplac_bmw_seria-5.csv" 

def init_driver():
    options = uc.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2} # Bez obrazków (szybciej)
    options.add_experimental_option("prefs", prefs)
    options.page_load_strategy = 'eager'
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    return driver

import json  # <--- WAŻNE: Dodaj to na samej górze pliku obok import re, time itd.

def wyciagnij_poprawna_cene(driver):
    """
    METODA PROFESJONALNA (JSON-LD):
    Pobiera cenę z danych strukturalnych ukrytych w kodzie strony (Schema.org).
    To eliminuje błędy typu "sklejenie nazwy modelu z ceną".
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # --- SPOSÓB 1: Dane strukturalne JSON (Najpewniejszy) ---
    try:
        # Szukamy wszystkich skryptów z danymi JSON-LD
        scripts = soup.find_all('script', {'type': 'application/ld+json'})
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                
                # Czasami JSON to lista, czasami słownik
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]
                    
                for item in items:
                    # Szukamy obiektu typu 'Offer' lub 'Product'/'Vehicle' zawierającego 'offers'
                    price = None
                    
                    # Wariant A: Bezpośrednio w obiekcie Offer
                    if item.get('@type') == 'Offer':
                        price = item.get('price')
                        
                    # Wariant B: Zagnieżdżone w offers
                    elif 'offers' in item:
                        offers = item['offers']
                        if isinstance(offers, dict):
                            price = offers.get('price')
                        elif isinstance(offers, list) and len(offers) > 0:
                            price = offers[0].get('price')
                            
                    if price:
                        return int(float(price)) # Konwersja na int (np. 70000.00 -> 70000)
                        
            except:
                continue
    except Exception as e:
        print(f"Błąd JSON: {e}")

    # --- SPOSÓB 2: Regex (Plan awaryjny - Inteligentne szukanie) ---
    # Jeśli JSON zawiedzie, szukamy tekstu, ale bierzemy TYLKO liczbę stojącą bezpośrednio przy "zł"
    try:
        # Znajdź wszystkie wystąpienia "zł" lub "PLN"
        text_content = soup.get_text()
        
        # Regex: Szukaj grupy cyfr (i spacji), która jest PRZED słowem "zł" lub "PLN"
        # Ignoruje cyfry stojące dalej (jak model "Seria 4")
        matches = re.findall(r'(\d[\d\s]*)\s*(?:zł|PLN|pln)', text_content)
        
        candidates = []
        for m in matches:
            clean = re.sub(r'\D', '', m) # Usuń spacje
            if not clean: continue
            val = int(clean)
            
            # Filtry logiczne
            if 1000 < val < 4000000: # Cena auta od 1k do 4mln
                candidates.append(val)
        
        # Zwróć największą sensowną liczbę (bo rata jest mała, cena duża)
        if candidates:
            return max(candidates)
            
    except Exception as e:
        print(f"Błąd Regex: {e}")

    return None

def main():
    if not os.path.exists(NAZWA_PLIKU_CSV):
        print(f"❌ Nie znaleziono pliku: {NAZWA_PLIKU_CSV}")
        return

    print(f"📂 Wczytuję plik: {NAZWA_PLIKU_CSV}")
    df = pd.read_csv(NAZWA_PLIKU_CSV, sep=';')
    
    # Sprawdzenie czy mamy kolumny Link i Cena
    if 'Link' not in df.columns:
        print("❌ Plik CSV nie ma kolumny 'Link'.")
        return

    driver = init_driver()
    licznik_zmian = 0
    
    print(f"🚀 Rozpoczynam naprawę cen dla {len(df)} rekordów...")

    try:
        for index, row in df.iterrows():
            link = row['Link']
            stara_cena = row['Cena']
            
            # Opcjonalnie: Naprawiamy tylko te, które wyglądają na podejrzanie niskie (np. < 5000 zł dla BMW)
            # Ale dla pewności lepiej sprawdzić wszystkie, chyba że masz ich tysiące.
            
            print(f"[{index+1}/{len(df)}] Sprawdzam: {link[-20:]} ... ", end="")
            
            try:
                driver.get(link)
                time.sleep(1) # Krótki czas na załadowanie
                
                nowa_cena = wyciagnij_poprawna_cene(driver)
                
                if nowa_cena:
                    # Jeśli nowa cena różni się od starej, aktualizujemy
                    # Uwaga: porównujemy jako liczby (trzeba oczyścić starą cenę z CSV jeśli jest stringiem)
                    stara_cena_num = int(re.sub(r'\D', '', str(stara_cena))) if pd.notnull(stara_cena) and str(stara_cena).strip() else 0
                    
                    if nowa_cena != stara_cena_num:
                        print(f"KOREKTA: {stara_cena} -> {nowa_cena}")
                        df.at[index, 'Cena'] = nowa_cena
                        licznik_zmian += 1
                        
                        # Zapisujemy co 10 rekordów, żeby nie stracić postępu
                        if licznik_zmian % 10 == 0:
                            df.to_csv(NAZWA_PLIKU_CSV, sep=';', index=False, encoding='utf-8-sig')
                    else:
                        print("OK (bez zmian)")
                else:
                    print("Brak ceny na stronie (pomijam)")
                    
            except Exception as e:
                print(f"Błąd przy linku: {e}")
                continue

    except KeyboardInterrupt:
        print("\n🛑 Przerwano przez użytkownika.")
    finally:
        # Zapis końcowy
        df.to_csv(NAZWA_PLIKU_CSV, sep=';', index=False, encoding='utf-8-sig')
        driver.quit()
        print(f"\n✅ Zakończono! Zaktualizowano cen w: {licznik_zmian} ofertach.")

if __name__ == "__main__":
    main()