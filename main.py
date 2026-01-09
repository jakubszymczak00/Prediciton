import argparse
import sys
import time
from utils.config import SAMOCHODY
from utils.drivers import init_driver
from utils.logger import log 
from utils.stats import SessionStats 
from db_manager import BazaDanych
from scrapers.otomoto import run_otomoto_scraper
from scrapers.autoplac import run_autoplac_scraper

def clear_console():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def interactive_menu():
    clear_console()
    print("==========================================")
    print("MEGA SCRAPER (MENU)")
    print("==========================================")
    
    print("\nDostepne marki:")
    sorted_brands = sorted(SAMOCHODY.items(), key=lambda x: int(x[0]))
    for k, v in sorted_brands:
        print(f"[{k}] {v['nazwa']}")
    
    brand_id = input("\nWybierz markę (numer): ")
    if brand_id not in SAMOCHODY:
        print("Blad: Niepoprawny numer marki.")
        return None, None, None

    selected_brand = SAMOCHODY[brand_id]
    
    print(f"\nWybrano: {selected_brand['nazwa']}")
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
        return None, None, None

    print("\n--- Wybierz platforme ---")
    print("[1] Otomoto + Autoplac")
    print("[2] Tylko Otomoto")
    print("[3] Tylko Autoplac")
    
    plat_choice = input("Wybór (Enter = 1): ")
    site = 'all'
    if plat_choice == '2': site = 'otomoto'
    elif plat_choice == '3': site = 'autoplac'
    
    return selected_brand['marka'], models_to_scrape, site

def main():
    parser = argparse.ArgumentParser(description="Scraper Ofert Samochodowych")
    parser.add_argument("--site", choices=['otomoto', 'autoplac', 'all'], help="Platforma")
    parser.add_argument("--brand", help="ID marki")
    parser.add_argument("--model", help="ID modelu")
    parser.add_argument("--auto", action="store_true", help="Tryb automatyczny")
    
    args = parser.parse_args()

    marka_nazwa = None
    models_to_scrape = []
    site_mode = 'all'

    if args.auto or args.brand:
        if not args.brand or args.brand not in SAMOCHODY:
            log.error("CLI: Bledne ID marki.")
            return
        brand_data = SAMOCHODY[args.brand]
        marka_nazwa = brand_data['marka']
        if args.model:
            if args.model in brand_data['modele']:
                models_to_scrape.append(brand_data['modele'][args.model])
            else:
                log.error("CLI: Bledne ID modelu.")
                return
        else:
            models_to_scrape = list(brand_data['modele'].values())
        if args.site: site_mode = args.site
    else:
        m, mods, s = interactive_menu()
        if not m: return
        marka_nazwa = m
        models_to_scrape = mods
        site_mode = s

    log.info(f"Start procesu. Marka: {marka_nazwa}, Modeli: {len(models_to_scrape)}")
    
    # Inicjalizacja statystyk i bazy
    stats = SessionStats()
    db = BazaDanych()
    driver = init_driver()

    try:
        for model_data in models_to_scrape:
            log.info(f"Przetwarzanie modelu: {marka_nazwa} {model_data['nazwa']}")
            
            # Autoplac
            if site_mode in ['autoplac', 'all']:
                slug = model_data.get('slug_auto')
                if slug:
                    # Przekazujemy obiekt stats do funkcji scrapujacej
                    run_autoplac_scraper(driver, db, stats, marka_nazwa, slug, model_data['nazwa'])
                else:
                    log.warning(f"Brak sluga Autoplac dla {model_data['nazwa']}")

            # Otomoto
            if site_mode in ['otomoto', 'all']:
                slug = model_data.get('slug_oto')
                if slug:
                    run_otomoto_scraper(driver, db, stats, marka_nazwa, slug, model_data['nazwa'])
                else:
                    log.warning(f"Brak sluga Otomoto dla {model_data['nazwa']}")
                    
    except KeyboardInterrupt:
        log.warning("Zatrzymano przez uzytkownika.")
    except Exception as e:
        log.error(f"Nieoczekiwany blad krytyczny: {e}")
    finally:
        driver.quit()
        log.info("Zakonczono prace przegladarki.")
        
        # Wyswietlenie i zapisanie raportu koncowego
        summary = stats.get_summary()
        print("\n" + summary)
        log.info(summary.replace("\n", " | ")) # W logu w jednej linii lub wg uznania

if __name__ == "__main__":
    main()