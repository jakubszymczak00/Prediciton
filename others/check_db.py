import sqlite3
import os

DB_NAME = "baza_pojazdow.db"

def check_database_health():
    if not os.path.exists(DB_NAME):
        print(f"❌ Błąd: Nie znaleziono pliku bazy danych: {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"\n{'='*40}")
    print(f"   RAPORT STANU BAZY DANYCH")
    print(f"{'='*40}")

    # 1. Całkowita liczba ofert
    cursor.execute("SELECT COUNT(*) FROM oferty")
    total_offers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM oferty WHERE is_active = 1")
    active_offers = cursor.fetchone()[0]

    print(f"📊 Łącznie ofert:     {total_offers}")
    print(f"🟢 Aktywne oferty:    {active_offers}")
    print(f"🔴 Zakończone oferty: {total_offers - active_offers}")
    print("-" * 40)

    if active_offers == 0:
        print("Brak aktywnych ofert do analizy.")
        conn.close()
        return

    # 2. Analiza braków w kluczowych kolumnach (dla aktywnych)
    # Kolumny do sprawdzenia
    columns_to_check = [
        ('generacja', 'Generacja'),
        ('wersja', 'Wersja'),
        ('naped', 'Napęd'),
        ('moc', 'Moc Silnika'),
        ('pojemnosc', 'Pojemność'),
        ('paliwo', 'Paliwo'),
        ('skrzynia', 'Skrzynia Biegów'),
        ('typ_sprzedawcy', 'Typ Sprzedawcy'),
        ('miasto', 'Miasto')
    ]

    print(f"{'KOLUMNA':<20} | {'BRAKI':<8} | {'% BRAKÓW'}")
    print("-" * 40)

    missing_stats = {}

    for col_db, col_name in columns_to_check:
        # Liczymy NULL lub puste stringi
        query = f"""
            SELECT COUNT(*) FROM oferty 
            WHERE is_active = 1 
            AND ({col_db} IS NULL OR {col_db} = '')
        """
        cursor.execute(query)
        missing_count = cursor.fetchone()[0]
        missing_stats[col_db] = missing_count
        
        percent = (missing_count / active_offers) * 100
        
        # Kolorowanie wyniku (jeśli dużo braków -> rzuca się w oczy)
        status_icon = ""
        if percent > 50: status_icon = "⚠️"
        elif percent == 0: status_icon = "✅"
        
        print(f"{col_name:<20} | {missing_count:<8} | {percent:.1f}% {status_icon}")

    print("-" * 40)

    # 3. Szacowanie czasu naprawy
    # Zakładamy, że naprawa dotyczy głównie Generacji i Napędu (najważniejsze)
    to_fix = max(missing_stats['generacja'], missing_stats['naped'])
    
    if to_fix > 0:
        seconds_per_car = 6 # 4s sleep + 2s ładowanie
        total_seconds = to_fix * seconds_per_car
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        print(f"\n🔧 DO NAPRAWY: ok. {to_fix} ofert (Generacja/Napęd).")
        print(f"⏱️ Szacowany czas naprawy: {int(hours)}h {int(minutes)}m (przy pracy non-stop).")
        print("💡 Sugestia: Uruchom repair_db.py na noc.")
    else:
        print("\n🎉 Gratulacje! Baza wygląda na kompletną w kluczowych polach.")

    conn.close()

if __name__ == "__main__":
    check_database_health()