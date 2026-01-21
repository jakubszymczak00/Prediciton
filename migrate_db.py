import sqlite3
import os

DB_NAME = "baza_pojazdow.db"

def wykonaj_migracje():
    if not os.path.exists(DB_NAME):
        print("Blad: Nie znaleziono pliku bazy danych!")
        return

    print(f"Rozpoczynam migracje bazy: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        # 1. Sprawdzamy, czy kolumna juz istnieje
        c.execute("PRAGMA table_info(oferty)")
        kolumny = [row[1] for row in c.fetchall()]
        
        if 'kategoria' in kolumny:
            print("Info: Kolumna 'kategoria' juz istnieje. Nie trzeba nic robic.")
        else:
            # 2. Dodajemy nowa kolumne
            print("Dodawanie kolumny 'kategoria'...")
            c.execute("ALTER TABLE oferty ADD COLUMN kategoria TEXT")
            
            # 3. Uzupelniamy stare rekordy (zakladamy, ze to co masz to osobowe)
            print("Aktualizacja starych rekordow na 'osobowe'...")
            c.execute("UPDATE oferty SET kategoria = 'osobowe' WHERE kategoria IS NULL")
            
            conn.commit()
            print("SUKCES: Baza zostala zaktualizowana!")
            
    except Exception as e:
        print(f"Wystapil blad podczas migracji: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    wykonaj_migracje()