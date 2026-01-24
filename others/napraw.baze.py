import sqlite3

DB_NAME = "baza_pojazdow.db"

def napraw():
    print(f"🔧 Rozpoczynam naprawę struktury bazy: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Lista nowych kolumn, których brakuje w Twojej starej bazie
    nowe_kolumny = [
        ("first_seen", "TIMESTAMP"),
        ("last_seen", "TIMESTAMP"),
        ("is_active", "INTEGER DEFAULT 1"),
        ("zrodlo_aktualizacja", "TEXT")
    ]

    print("--- Dodawanie brakujących kolumn ---")
    for nazwa, typ in nowe_kolumny:
        try:
            c.execute(f"ALTER TABLE oferty ADD COLUMN {nazwa} {typ}")
            print(f"✅ Dodano kolumnę: {nazwa}")
        except sqlite3.OperationalError:
            print(f"ℹ️ Kolumna {nazwa} już istnieje (pomijam)")

    # 2. Tworzenie tabeli historii (jeśli jej nie masz)
    print("\n--- Weryfikacja tabeli historii ---")
    c.execute('''
        CREATE TABLE IF NOT EXISTS historia_cen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oferta_id INTEGER,
            cena INTEGER,
            przebieg INTEGER,
            data_zmiany TIMESTAMP,
            FOREIGN KEY(oferta_id) REFERENCES oferty(id)
        )
    ''')
    print("✅ Tabela 'historia_cen' jest gotowa.")

    # 3. Uzupełnienie pustych danych w starych rekordach
    print("\n--- Uzupełnianie danych (Backfill) ---")
    c.execute("UPDATE oferty SET first_seen = data_dodania WHERE first_seen IS NULL")
    c.execute("UPDATE oferty SET last_seen = ostatnia_aktualizacja WHERE last_seen IS NULL")
    c.execute("UPDATE oferty SET is_active = 1 WHERE is_active IS NULL")
    print("✅ Uzupełniono daty i statusy w starych rekordach.")

    conn.commit()
    conn.close()
    print("\n🎉 GOTOWE! Możesz uruchomić main.py")

if __name__ == "__main__":
    napraw()