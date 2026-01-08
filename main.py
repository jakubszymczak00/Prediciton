import argparse
import sys
import time
from utils.config import SAMOCHODY
from utils.drivers import init_driver
from db_manager import BazaDanych
from scrapers.otomoto import run_otomoto_scraper
from scrapers.autoplac import run_autoplac_scraper

def clear_console():
    # Prosta funkcja czyszczaca ekran (Windows/Linux)
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def interactive_menu():
    """Wyswietla interaktywne menu wyboru marki i modelu"""
    clear_console()
    print("==========================================")
    print(" 🚗 MEGA SCRAPER (MENU) 🚗")
    print("==========================================")
    
    # 1. Wybor Marki
    print("\nDostepne marki:")
    sorted_brands = sorted(SAMOCHODY.items(), key=lambda x: int(x[0]))
    for k, v in sorted_brands:
        print(f"[{k}] {v['nazwa']}")
    
    brand_id = input("\nWybierz markę (numer): ")
    if brand_id not in SAMOCHODY:
        print("❌ Blad: Niepoprawny numer marki.")
        return None, None, None

    selected_brand = SAMOCHODY[brand_id]
    
    # 2. Wybor Modelu
    print(f"\n--- Wybrano: {selected_brand['nazwa']} ---")
    print("Dostepne modele:")
    print("[0] WSZYSTKIE MODELE (Pobierz cala marke)")
    
    sorted_models = sorted(selected_brand['modele'].items(), key=lambda x: int(x[0]))
    for k, v in sorted_models:
        print(f"[{k}] {v['nazwa']}")
        
    model_id = input("\nWybierz model (numer): ")
    
    models_to_scrape = []
    
    if model_id == "0":
        # Pobieramy wszystko
        models_to_scrape = list(selected_brand['modele'].values())
    elif model_id in selected_brand['modele']:
        # Pobieramy konkretny
        models_to_scrape.append(selected_brand['modele'][model_id])
    else:
        print("❌ Blad: Niepoprawny numer modelu.")
        return None, None, None

    # 3. Wybor Platformy
    print("\n--- Wybierz platforme ---")
    print("[1] Otomoto + Autoplac (Domyslnie)")
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
    parser.add_argument("--auto", action="store_true", help="Pomin menu, uzyj argumentow")
    
    args = parser.parse_args()

    marka_nazwa = None
    models_to_scrape = []
    site_mode = 'all'

    # --- TRYB AUTOMATYCZNY (CLI) ---
    if args.auto or args.brand:
        if not args.brand or args.brand not in SAMOCHODY:
            print("❌ Blad CLI: Musisz podac poprawne --brand ID.")
            return
            
        brand_data = SAMOCHODY[args.brand]
        marka_nazwa = brand_data['marka']
        
        if args.model:
            if args.model in brand_data['modele']:
                models_to_scrape.append(brand_data['modele'][args.model])
            else:
                print("❌ Blad CLI: Bledne ID modelu.")
                return
        else:
            models_to_scrape = list(brand_data['modele'].values())
            
        if args.site:
            site_mode = args.site

    # --- TRYB INTERAKTYWNY (MENU) ---
    else:
        m, mods, s = interactive_menu()
        if not m: return # Uzytkownik anulowal
        marka_nazwa = m
        models_to_scrape = mods
        site_mode = s

    # --- URUCHOMIENIE SCRAPERA ---
    print(f"\n🚀 Startujemy! Marka: {marka_nazwa.upper()}, Liczba modeli: {len(models_to_scrape)}")
    
    db = BazaDanych()
    driver = init_driver()

    try:
        for model_data in models_to_scrape:
            print(f"\n" + "="*40)
            print(f"🔎 PRZETWARZANIE: {marka_nazwa.upper()} {model_data['nazwa'].upper()}")
            print("="*40)
            
            # 1. Autoplac
            if site_mode in ['autoplac', 'all']:
                slug = model_data.get('slug_auto')
                if slug:
                    run_autoplac_scraper(driver, db, marka_nazwa, slug, model_data['nazwa'])
                else:
                    print("⚠️ Brak sluga Autoplac dla tego modelu.")

            # 2. Otomoto
            if site_mode in ['otomoto', 'all']:
                slug = model_data.get('slug_oto')
                if slug:
                    run_otomoto_scraper(driver, db, marka_nazwa, slug, model_data['nazwa'])
                else:
                    print("⚠️ Brak sluga Otomoto dla tego modelu.")
                    
    except KeyboardInterrupt:
        print("\n🛑 Zatrzymano przez uzytkownika.")
    except Exception as e:
        print(f"\n❌ Wystapil niespodziewany blad: {e}")
    finally:
        driver.quit()
        print("\n👋 Zakonczono prace. Dane sa w bazie.")

if __name__ == "__main__":
    main()