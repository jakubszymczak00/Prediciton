import sqlite3
import os

DB_NAME = "baza_pojazdow.db"

def wyczysc_dostawcze():
    if not os.path.exists(DB_NAME):
        print("Brak pliku bazy danych.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        # Sprawdzamy ile jest dostawczych przed usunieciem
        c.execute("SELECT COUNT(*) FROM oferty WHERE kategoria = 'dostawcze'")
        count_before = c.fetchone()[0]
        print(f"Znaleziono {count_before} ofert w kategorii 'dostawcze'.")

        if count_before > 0:
            # Usuwamy
            c.execute("DELETE FROM oferty WHERE kategoria = 'dostawcze'")
            conn.commit()
            print(f"SUKCES: Usunięto {count_before} rekordów.")
            
            # Opcjonalnie: odkurzanie bazy (zmniejsza rozmiar pliku)
            c.execute("VACUUM") 
            print("Baza została uporządkowana (VACUUM).")
        else:
            print("Nie ma nic do usunięcia.")

    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    wyczysc_dostawcze()