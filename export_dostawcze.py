import sqlite3
import pandas as pd
import os

DB_NAME = "baza_pojazdow.db"
OUTPUT_FILE = "dostawcze_analiza.csv"

def eksportuj_dostawcze():
    if not os.path.exists(DB_NAME):
        print(f"Blad: Nie znaleziono bazy danych {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    
    # Pobieramy wszystko, co ma kategorie 'dostawcze'
    # Sortujemy po dacie dodania, zeby widziec najnowsze (te po poprawkach) na gorze
    query = """
    SELECT * FROM oferty 
    WHERE kategoria = 'dostawcze'
    ORDER BY id DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("Uwaga: Nie znaleziono zadnych ofert w kategorii 'dostawcze'.")
        else:
            # Zapis do CSV z kodowaniem utf-8-sig (zeby Excel widzial polskie znaki)
            df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            
            print(f"\nSUKCES! Wyeksportowano {len(df)} ofert.")
            print(f"Plik zapisany jako: {OUTPUT_FILE}")
            print("-" * 30)
            print("Podglad ostatnich 5 wpisow:")
            print(df[['platforma', 'marka', 'model', 'tytul', 'cena', 'nadwozie']].head().to_string(index=False))

    except Exception as e:
        print(f"Wystapil blad: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    eksportuj_dostawcze()