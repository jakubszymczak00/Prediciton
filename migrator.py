import pandas as pd
import glob
import re
import os
from db_manager import BazaDanych

# --- KONFIGURACJA ---
SEPARATOR_CSV = ';'

def clean_number(val):
    """
    Super-bezpieczne czyszczenie liczb z CSV.
    Obsługuje spacje 'miękkie' ( ), 'twarde' (\xa0) i inne śmieci.
    """
    if pd.isna(val) or val == '':
        return 0
    
    # KROK 1: Zamiana na tekst
    txt = str(val)
    
    # KROK 2: Usunięcie WSZYSTKICH rodzajów spacji i białych znaków
    # \s+ oznacza "dowolny biały znak" (spacja, tabulator, twarda spacja)
    txt_no_spaces = re.sub(r'\s+', '', txt)
    
    # KROK 3: Usunięcie wszystkiego co nie jest cyfrą (np. 'km', 'PLN', liter)
    nums = re.sub(r'\D', '', txt_no_spaces)
    
    # KROK 4: Bezpiecznik na puste wartości po czyszczeniu
    if not nums:
        return 0
        
    return int(nums)

def safe_str(val):
    """Zabezpiecza przed wartościami 'nan' (puste komórki)"""
    if pd.isna(val): return ""
    return str(val).strip()

def wykryj_platforme(url):
    """Rozpoznaje serwis po linku"""
    url_lower = str(url).lower()
    if 'otomoto.pl' in url_lower:
        return 'otomoto'
    elif 'autoplac.pl' in url_lower:
        return 'autoplac'
    else:
        return 'autoplac' # Domyślnie autoplac dla Twoich starych plików

def mapuj_wiersz(row):
    """Przetwarza wiersz z CSV na format bazy"""
    
    # 1. Pobieramy Link
    url = row.get('Link')
    if pd.isna(url) or 'http' not in str(url):
        return None

    # 2. Wykrywamy platformę
    platforma = wykryj_platforme(url)

    # 3. Budujemy Tytuł
    marka = safe_str(row.get('Marka pojazdu'))
    model = safe_str(row.get('Model pojazdu'))
    generacja = safe_str(row.get('Generacja'))
    if generacja.lower() == 'nan': generacja = ''
    
    tytul = f"{marka} {model} {generacja}".strip()

    # 4. Mapowanie Kolumn (CSV -> Baza)
    dane = {
        'url': url.strip(),
        'platforma': platforma,
        'tytul': tytul,
        'cena': clean_number(row.get('Cena')),
        'zrodlo_aktualizacja': safe_str(row.get('Data_Aktualizacji')),

        'marka': marka,
        'model': model,
        'wersja': safe_str(row.get('Wersja')),
        'generacja': generacja,
        'rocznik': clean_number(row.get('Rok produkcji')),
        'przebieg': clean_number(row.get('Przebieg')), # Tu był problem ze spacjami
        'paliwo': safe_str(row.get('Rodzaj paliwa')),
        'pojemnosc': clean_number(row.get('Pojemność skokowa')),
        'moc': clean_number(row.get('Moc')),
        'nadwozie': safe_str(row.get('Typ nadwozia')),
        'kolor': safe_str(row.get('Rodzaj koloru')),
        'skrzynia': safe_str(row.get('Skrzynia biegów')),
        'naped': safe_str(row.get('Napęd')),
        'kraj': safe_str(row.get('Kraj pochodzenia')),
        'zarejestrowany': safe_str(row.get('Zarejestrowany w Polsce')),
        'nr_rejestracyjny': safe_str(row.get('Ma numer rejestracyjny'))
    }
    return dane

def main():
    print("🚀 START POPRAWIONEJ MIGRACJI (FIX SPACJI W LICZBACH)...")
    
    # 1. Połączenie z bazą
    db = BazaDanych("baza_pojazdow.db")
    
    # 2. Szukanie plików CSV
    pliki = glob.glob("*.csv")
    
    if not pliki:
        print("❌ Nie znaleziono plików .csv")
        return

    total_rows = 0
    
    for plik in pliki:
        print(f"\n📂 Przetwarzanie pliku: {plik}")
        try:
            # Wczytanie CSV
            df = pd.read_csv(plik, sep=SEPARATOR_CSV)
            
            if 'Link' not in df.columns:
                print("   ⚠️ Brak kolumny 'Link' - pomijam.")
                continue
            
            added = 0
            for index, row in df.iterrows():
                dane = mapuj_wiersz(row)
                if dane:
                    db.upsert_oferta(dane)
                    added += 1
                    total_rows += 1
            
            print(f"   ✅ Zapisano: {added} aut.")
            
        except Exception as e:
            print(f"   ❌ Błąd pliku: {e}")

    print(f"\n🎉 SUKCES! W bazie znajduje się teraz {total_rows} aut.")
    print("   Problem ze spacjami w liczbach (np. '93 000') został rozwiązany.")

if __name__ == "__main__":
    main()