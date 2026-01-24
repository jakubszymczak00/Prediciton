import sqlite3

DB_NAME = "baza_pojazdow.db"

def wykonaj_migracje():
    print(f"🔧 Rozpoczynam aktualizację bazy (Lista 3 - Value Boost)...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    nowe_kolumny = [
        ("miasto", "TEXT"),
        ("wojewodztwo", "TEXT"),
        ("typ_sprzedawcy", "TEXT"),  # Dealer / Osoba prywatna
        ("liczba_zdjec", "INTEGER"),
        ("liczba_opcji", "INTEGER"), # Ile elementów wyposażenia
        ("wyposazenie", "TEXT"),     # Lista po przecinku: "ABS, Klimatyzacja..."
        ("opis", "TEXT")             # Pełny opis tekstowy
    ]

    for nazwa, typ in nowe_kolumny:
        try:
            c.execute(f"ALTER TABLE oferty ADD COLUMN {nazwa} {typ}")
            print(f"✅ Dodano kolumnę: {nazwa}")
        except sqlite3.OperationalError:
            print(f"ℹ️ Kolumna {nazwa} już istnieje.")

    conn.commit()
    conn.close()
    print("\n🎉 Baza gotowa na nowe dane!")

if __name__ == "__main__":
    wykonaj_migracje()