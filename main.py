import argparse
import sys
import time
import os

# Importy konfiguracji i narzedzi
from utils.config import SAMOCHODY, DOSTAWCZE, ROK_OD_OSOBOWE, ROK_OD_DOSTAWCZE
from utils.drivers import init_driver # Zakładam, że masz ten plik
from utils.logger import log 
from utils.stats import SessionStats 
from db_manager import BazaDanych # Zakładam, że masz ten plik

# Importy scraperow (TE NOWE, POPRAWIONE)
from scrapers.otomoto import run_otomoto_scraper
from scrapers.autoplac import run_autoplac_scraper

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def interactive_menu():
    """
    Interaktywne menu wyboru kategorii, marki, modelu i platformy.
    """
    clear_console()
    print("==========================================")
    print("   MEGA SCRAPER - DANIEL V2 (PREDYKCJA)   ")
    print("==========================================")
    
    # --- KROK 1: Wybor kategorii ---
    print("\nWybierz kategorie pojazdow:")
    print(f"[1] Samochody Osobowe   (od rocznika {ROK_OD_OSOBOWE})")
    print(f"[2] Samochody Dostawcze (od rocznika {ROK_OD_DOSTAWCZE})")
    
    cat_choice = input("\nWybor (domyslnie 1): ")
    
    # Domyslne ustawienia (Osobowe)
    baza_modeli = SAMOCHODY
    oto_cat = "osobowe"              # slug dla Otomoto
    auto_cat = "samochody-osobowe"   # slug dla Autoplac
    wybrany_rok = ROK_OD_OSOBOWE
    typ_nazwa = "OSOBOWE"
    
    # Nadpisanie jesli wybrano Dostawcze
    if cat_choice == '2':
        baza_modeli = DOSTAWCZE
        oto_cat = "dostawcze"        
        auto_cat = "samochody-dostawcze" # Poprawny slug dla Autoplac
        wybrany_rok = ROK_OD_DOSTAWCZE
        typ_nazwa = "DOSTAWCZE"
        print(f"\n--- Tryb: {typ_nazwa} ---")
    else:
        print(f"\n--- Tryb: {typ_nazwa} ---")

    # --- KROK 2: Wybor marki ---
    print("\nDostepne marki:")
    # Sortowanie kluczy numerycznie
    sorted_brands = sorted(baza_modeli.items(), key=lambda x: int(x[0]))
    
    for k, v in sorted_brands:
        print(f"[{k}] {v['nazwa']}")
    
    brand_id = input("\nWybierz markę (numer): ")
    if brand_id not in baza_modeli:
        print("Blad: Niepoprawny numer marki.")
        return None

    selected_brand = baza_modeli[brand_id]
    
    # --- KROK 3: Wybor modelu ---
    print(f"\nWybrano marke: {selected_brand['nazwa']}")
    print("Dostepne modele:")
    print("[0] WSZYSTKIE MODELE")
    
    sorted_models = sorted(selected_brand['modele'].items(), key=lambda x: int(x[0]))
    for k, v in sorted_models:
        print(f"[{k}] {v['nazwa']}")
        
    model_id = input("\nWybierz model (numer): ")
    models_to_scrape = []
    
    if model_id == "0":
        models_to_scrape = list(selected_brand['modele'].values())
    elif model_id in selected_brand['modele']:
        models_to_scrape.append(selected_brand['modele'][model_id])
    else:
        print("Blad: Niepoprawny numer modelu.")
        return None

    # --- KROK 4: Wybor platformy ---
    print("\n--- Wybierz platforme ---")
    print("[1] Otomoto + Autoplac (Zalecane)")
    print("[2] Tylko Otomoto")
    print("[3] Tylko Autoplac")
    
    plat_choice = input("Wybór (Enter = 1): ")
    site = 'all'
    if plat_choice == '2': site = 'otomoto'
    elif plat_choice == '3': site = 'autoplac'
    
    return selected_brand['marka'], models_to_scrape, site, oto_cat, auto_cat, wybrany_rok

def main():
    parser = argparse.ArgumentParser(description="Scraper Ofert Samochodowych")
    args = parser.parse_args()

    wynik_menu = interactive_menu()
    
    if not wynik_menu:
        log.info("Anulowano lub blad wyboru.")
        return

    marka_nazwa, models_to_scrape, site_mode, oto_cat, auto_cat, rok_od = wynik_menu

    log.info(f"START PROCESU. Kategoria: {oto_cat.upper()} | Rok od: {rok_od} | Marka: {marka_nazwa}")
    log.info(f"Liczba modeli do sprawdzenia: {len(models_to_scrape)}")
    
    stats = SessionStats()
    db = BazaDanych()
    driver = init_driver()

    try:
        for model_data in models_to_scrape:
            log.info(f"--- Przetwarzanie modelu: {marka_nazwa} {model_data['nazwa']} ---")
            
            # --- AUTOPLAC ---
            if site_mode in ['autoplac', 'all']:
                slug = model_data.get('slug_auto')
                if slug:
                    run_autoplac_scraper(
                        driver=driver, 
                        db=db, 
                        stats=stats, 
                        marka=marka_nazwa, 
                        model_slug=slug, 
                        model_nazwa=model_data['nazwa'],
                        kategoria_url=auto_cat, 
                        rok_od=rok_od
                    )
                else:
                    log.warning(f"Brak sluga Autoplac dla {model_data['nazwa']}")

            # --- OTOMOTO ---
            if site_mode in ['otomoto', 'all']:
                slug = model_data.get('slug_oto')
                if slug:
                    run_otomoto_scraper(
                        driver=driver, 
                        db=db, 
                        stats=stats, 
                        marka=marka_nazwa, 
                        model_slug=slug, 
                        model_nazwa=model_data['nazwa'],
                        kategoria=oto_cat, 
                        rok_od=rok_od
                    )
                else:
                    log.warning(f"Brak sluga Otomoto dla {model_data['nazwa']}")

        # --- FINALIZACJA ---
        log.info("--- Zakonczono pobieranie. Weryfikacja aktywnosci ofert ---")
        zamkniete = db.oznacz_zakonczone_oferty()
        log.info(f"Zaktualizowano status {zamkniete} ofert na 'zakonczone'.")

    except KeyboardInterrupt:
        log.warning("Proces zatrzymany przez uzytkownika (Ctrl+C).")
    except Exception as e:
        log.error(f"Wystapil nieoczekiwany blad krytyczny: {e}")
    finally:
        driver.quit()
        db.close()
        summary = stats.get_summary()
        print("\n" + str(summary))
        log.info("Zakonczono prace.")

if __name__ == "__main__":
    main()