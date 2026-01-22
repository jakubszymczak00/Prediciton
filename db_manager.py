import sqlite3
from datetime import datetime

class BazaDanych:
    def __init__(self, nazwa_pliku="baza_pojazdow.db"):
        self.nazwa_pliku = nazwa_pliku
        # Otwieramy połączenie RAZ i trzymamy je otwarte
        self.conn = sqlite3.connect(self.nazwa_pliku, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.stworz_tabele()

    def stworz_tabele(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS oferty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                platforma TEXT,
                tytul TEXT,
                cena INTEGER,
                
                kategoria TEXT, 
                marka TEXT, model TEXT, wersja TEXT, generacja TEXT,
                rocznik INTEGER, przebieg INTEGER, paliwo TEXT,
                pojemnosc INTEGER, moc INTEGER,
                nadwozie TEXT, kolor TEXT, skrzynia TEXT, naped TEXT,
                kraj TEXT, zarejestrowany TEXT, nr_rejestracyjny TEXT,
                
                miasto TEXT, wojewodztwo TEXT, typ_sprzedawcy TEXT,
                liczba_zdjec INTEGER, liczba_opcji INTEGER,
                wyposazenie TEXT, opis TEXT,
                
                zrodlo_aktualizacja TEXT,
                data_dodania TIMESTAMP,
                ostatnia_aktualizacja TIMESTAMP,
                first_seen TIMESTAMP, last_seen TIMESTAMP, is_active INTEGER DEFAULT 1
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historia_cen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oferta_id INTEGER,
                cena INTEGER,
                przebieg INTEGER,
                data_zmiany TIMESTAMP,
                FOREIGN KEY(oferta_id) REFERENCES oferty(id)
            )
        ''')
        self.conn.commit()
        # WAŻNE: Nie zamykamy tutaj połączenia!

    def upsert_oferta(self, dane):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "ERROR"

        try:
            # Używamy self.cursor zamiast tworzyć nowy
            self.cursor.execute("SELECT id, cena FROM oferty WHERE url = ?", (dane['url'],))
            row = self.cursor.fetchone()

            if row is None:
                # --- INSERT (Nowa oferta) ---
                self.cursor.execute('''
                    INSERT INTO oferty (
                        url, platforma, tytul, cena, przebieg, rocznik,
                        kategoria, marka, model, wersja, generacja, paliwo, pojemnosc, moc,
                        nadwozie, kolor, skrzynia, naped, kraj, zarejestrowany, nr_rejestracyjny,
                        miasto, wojewodztwo, typ_sprzedawcy, liczba_zdjec, liczba_opcji, wyposazenie, opis,
                        zrodlo_aktualizacja, data_dodania, ostatnia_aktualizacja, first_seen, last_seen, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    dane.get('url'), dane.get('platforma'), dane.get('tytul'), dane.get('cena'), 
                    dane.get('przebieg'), dane.get('rocznik'),
                    dane.get('kategoria'),
                    dane.get('marka'), dane.get('model'), dane.get('wersja'), dane.get('generacja'),
                    dane.get('paliwo'), dane.get('pojemnosc'), dane.get('moc'),
                    dane.get('nadwozie'), dane.get('kolor'), dane.get('skrzynia'), dane.get('naped'),
                    dane.get('kraj'), dane.get('zarejestrowany'), dane.get('nr_rejestracyjny'),
                    dane.get('miasto'), dane.get('wojewodztwo'), dane.get('typ_sprzedawcy'),
                    dane.get('liczba_zdjec'), dane.get('liczba_opcji'), dane.get('wyposazenie'), dane.get('opis'),
                    dane.get('zrodlo_aktualizacja', ''), now, now, now, now
                ))
                new_id = self.cursor.lastrowid
                
                # Zapisz cenę początkową w historii
                self.cursor.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                                  (new_id, dane.get('cena'), dane.get('przebieg'), now))
                status = "INSERT"
            else:
                # --- UPDATE (Istniejąca oferta) ---
                db_id, old_cena = row
                
                # Zawsze odświeżamy last_seen
                self.cursor.execute("UPDATE oferty SET last_seen = ?, is_active = 1 WHERE id = ?", (now, db_id))
                status = "SEEN"

                # Jeśli cena się zmieniła
                if old_cena != dane['cena']:
                    self.cursor.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                                      (db_id, dane['cena'], dane['przebieg'], now))
                    status = "UPDATE_PRICE"

                # WAŻNE: Aktualizujemy też dane techniczne (bo scraper mógł wejść w szczegóły i znaleźć generację)
                self.cursor.execute('''
                    UPDATE oferty SET 
                        cena = ?, przebieg = ?, rocznik = ?, tytul = ?, kategoria = ?,
                        miasto = ?, wojewodztwo = ?, typ_sprzedawcy = ?,
                        liczba_zdjec = ?, liczba_opcji = ?, wyposazenie = ?, opis = ?,
                        
                        marka = ?, model = ?, wersja = ?, generacja = ?,
                        paliwo = ?, pojemnosc = ?, moc = ?,
                        nadwozie = ?, kolor = ?, skrzynia = ?, naped = ?,
                        kraj = ?, zarejestrowany = ?, nr_rejestracyjny = ?,
                        
                        zrodlo_aktualizacja = ?, ostatnia_aktualizacja = ?
                    WHERE id = ?
                ''', (
                    dane['cena'], dane['przebieg'], dane['rocznik'], dane['tytul'], dane.get('kategoria'),
                    dane.get('miasto'), dane.get('wojewodztwo'), dane.get('typ_sprzedawcy'),
                    dane.get('liczba_zdjec'), dane.get('liczba_opcji'), dane.get('wyposazenie'), dane.get('opis'),
                    
                    dane.get('marka'), dane.get('model'), dane.get('wersja'), dane.get('generacja'),
                    dane.get('paliwo'), dane.get('pojemnosc'), dane.get('moc'),
                    dane.get('nadwozie'), dane.get('kolor'), dane.get('skrzynia'), dane.get('naped'),
                    dane.get('kraj'), dane.get('zarejestrowany'), dane.get('nr_rejestracyjny'),
                    
                    dane.get('zrodlo_aktualizacja'), now, db_id
                ))

            self.conn.commit()
        except Exception as e:
            print(f"Blad SQL: {e}")
            status = "ERROR"
        
        return status

    def oznacz_zakonczone_oferty(self):
        self.cursor.execute('''
            UPDATE oferty 
            SET is_active = 0 
            WHERE is_active = 1 
            AND (julianday('now') - julianday(last_seen)) > 1.0
        ''')
        count = self.cursor.rowcount
        self.conn.commit()
        return count

    # --- TEGO BRAKOWAŁO: ---
    def close(self):
        """Bezpiecznie zamyka połączenie z bazą."""
        if self.conn:
            self.conn.close()