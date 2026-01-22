import sqlite3
import pandas as pd
import os

DB_NAME = "baza_pojazdow.db"
CSV_NAME = "dane_dashboard.csv"

def eksportuj_do_lookera():
    if not os.path.exists(DB_NAME):
        print(f"Blad: Nie znaleziono pliku {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # Dodano 'generacja' i 'wersja' do SELECT
    query = """
    SELECT 
        id, platforma, kategoria, marka, model, 
        generacja, wersja, -- <--- TEGO BRAKOWALO
        tytul, cena, przebieg, rocznik, 
        paliwo, pojemnosc, moc, skrzynia, naped,
        miasto, wojewodztwo, typ_sprzedawcy, liczba_zdjec, liczba_opcji,
        data_dodania, ostatnia_aktualizacja, first_seen, last_seen, url, is_active,
        CASE WHEN is_active = 1 THEN 'Aktywna' ELSE 'Zakonczona' END as status_oferty,
        CAST((julianday(last_seen) - julianday(first_seen)) AS INTEGER) as dni_na_rynku
    FROM oferty
    WHERE cena IS NOT NULL AND cena > 1000
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("Baza jest pusta lub brak ofert powyżej 1000 PLN.")
            return

        # --- CZYSZCZENIE DANYCH ---
        values_to_fill = {
            'kategoria': 'osobowe',
            'miasto': 'Nieznane',
            'wojewodztwo': 'Nieznane',
            'typ_sprzedawcy': 'Nieokreslony',
            'paliwo': 'Inne',
            'generacja': 'Nieznana', # Ważne dla dashboardu
            'wersja': 'Standard',
            'liczba_zdjec': 0,
            'liczba_opcji': 0,
            'moc': 0,
            'pojemnosc': 0
        }
        df = df.fillna(values_to_fill)
        
        # --- SEGMENTACJA PRZEBIEGU ---
        def segment_przebiegu(km):
            if pd.isna(km) or km == 0: return "Brak danych"
            km = int(km)
            if km < 50000: return "0 - 50k km"
            if km < 100000: return "50k - 100k km"
            if km < 150000: return "100k - 150k km"
            if km < 200000: return "150k - 200k km"
            if km < 300000: return "200k - 300k km"
            return "300k+ km"
            
        df['segment_przebiegu'] = df['przebieg'].apply(segment_przebiegu)

        # --- SEGMENTACJA CENOWA (Nowość - przydatne w Lookerze) ---
        def segment_ceny(cena):
            if pd.isna(cena) or cena == 0: return "Brak"
            c = int(cena)
            if c < 30000: return "Do 30k PLN"
            if c < 60000: return "30k - 60k PLN"
            if c < 100000: return "60k - 100k PLN"
            if c < 200000: return "100k - 200k PLN"
            return "Powyżej 200k PLN"

        df['segment_ceny'] = df['cena'].apply(segment_ceny)

        # Formatowanie daty (usuwa godziny dla czytelności w Excelu/CSV)
        for date_col in ['data_dodania', 'ostatnia_aktualizacja', 'first_seen', 'last_seen']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')

        # Zapis do CSV
        df.to_csv(CSV_NAME, index=False, encoding='utf-8-sig', sep=',')
        print(f"✅ Eksport zakonczony pomyślnie.")
        print(f"📂 Plik: {CSV_NAME}")
        print(f"📊 Liczba ofert: {len(df)}")
        print(f"   (W tym z generacją: {len(df[df['generacja'] != 'Nieznana'])})")

    except Exception as e:
        print(f"❌ Blad eksportu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    eksportuj_do_lookera()