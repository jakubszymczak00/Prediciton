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
    
    # Dodano pole 'kategoria' do SELECT
    query = """
    SELECT 
        id, platforma, kategoria, marka, model, tytul, cena, przebieg, rocznik, 
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
        
        # Czyszczenie NULLi
        df['kategoria'] = df['kategoria'].fillna('osobowe') # Zabezpieczenie
        df['miasto'] = df['miasto'].fillna('Nieznane')
        df['wojewodztwo'] = df['wojewodztwo'].fillna('Nieznane')
        df['typ_sprzedawcy'] = df['typ_sprzedawcy'].fillna('Nieokreslony')
        df['paliwo'] = df['paliwo'].fillna('Inne')
        df['liczba_zdjec'] = df['liczba_zdjec'].fillna(0)
        df['liczba_opcji'] = df['liczba_opcji'].fillna(0)
        
        def segment_przebiegu(km):
            if pd.isna(km) or km == 0: return "Brak danych"
            if km < 50000: return "0 - 50k km"
            if km < 100000: return "50k - 100k km"
            if km < 150000: return "100k - 150k km"
            if km < 200000: return "150k - 200k km"
            return "200k+ km"
            
        df['segment_przebiegu'] = df['przebieg'].apply(segment_przebiegu)

        df.to_csv(CSV_NAME, index=False, encoding='utf-8-sig')
        print(f"Eksport zakonczony. Utworzono plik: {CSV_NAME}")
        print(f"Liczba ofert: {len(df)}")

    except Exception as e:
        print(f"Blad eksportu: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    eksportuj_do_lookera()