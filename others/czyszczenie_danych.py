import sqlite3

DB_NAME = "baza_pojazdow.db"

# KONFIGURACJA LOGIKI CZYSZCZENIA
MIN_CENA = 15000       # Poniżej tego to pewnie "odstępne leasingowe", złom lub błąd (dla aut 2017+)
MAX_PRZEBIEG = 500000  # Powyżej tego to zazwyczaj błąd wpisywania (dla aut 7-letnich)
MIN_MOC = 50           # Mniej niż 50 KM w nowoczesnym aucie to błąd
MIN_POJEMNOSC = 800    # Mniej niż 0.8L to błąd (chyba że elektryk)

def wyczysc_syf():
    print("🧹 Rozpoczynam GLĘBOKIE czyszczenie bazy danych...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    deleted_count = 0

    # 1. USUWANIE "CENY LEASINGOWEJ" I "PLACEHOLDERÓW"
    # Auta z rocznika 2017+ rzadko kosztują mniej niż 15k. Jeśli tak - to podejrzane.
    print(f"   🔍 Usuwam oferty z ceną poniżej {MIN_CENA} PLN (podejrzenie leasingu/błędu)...")
    c.execute(f"DELETE FROM oferty WHERE cena < {MIN_CENA}")
    deleted_count += c.rowcount

    # 2. USUWANIE KOSMICZNYCH PRZEBIEGÓW
    print(f"   🔍 Usuwam przebiegi powyżej {MAX_PRZEBIEG} km (literówki)...")
    c.execute(f"DELETE FROM oferty WHERE przebieg > {MAX_PRZEBIEG}")
    deleted_count += c.rowcount

    # 3. USUWANIE BŁĘDÓW TECHNICZNYCH (Moc/Pojemność)
    # Uwaga: Wykluczamy elektryki z filtra pojemności (bo mają 0)
    print("   🔍 Usuwam błędne dane techniczne (Moc < 50KM, Pojemność < 800cm3)...")
    c.execute(f"""
        DELETE FROM oferty 
        WHERE moc < {MIN_MOC} 
        OR (paliwo NOT LIKE '%Elektryczny%' AND pojemnosc < {MIN_POJEMNOSC})
    """)
    deleted_count += c.rowcount

    # 4. USUWANIE PO SŁOWACH KLUCZOWYCH (Uszkodzone/Angliki ukryte w tytule)
    # SQL 'LIKE' szuka fragmentów tekstu
    syf_slowa = ['%uszkodz%', '%rozbit%', '%anglik%', '%odstępn%', '%przejęci%', '%rat%', '%wrak%']
    
    print("   🔍 Usuwam ukryte uszkodzone/angliki/leasingi po tytule...")
    for slowo in syf_slowa:
        c.execute(f"DELETE FROM oferty WHERE tytul LIKE '{slowo}'")
        deleted_count += c.rowcount
        # Opcjonalnie sprawdzamy też opis (może być wolne, odkomentuj jeśli chcesz)
        # c.execute(f"DELETE FROM oferty WHERE opis LIKE '{slowo}'")
        # deleted_count += c.rowcount

    conn.commit()
    conn.close()
    
    print("-" * 40)
    print(f"✅ SKOŃCZONE. Łącznie usunięto {deleted_count} śmieciowych rekordów.")
    print("   Twoja baza jest teraz krystalicznie czysta analitycznie.")

if __name__ == "__main__":
    wyczysc_syf()