import sqlite3
from datetime import datetime

class BazaDanych:
    def __init__(self, nazwa_pliku="baza_pojazdow.db"):
        self.nazwa_pliku = nazwa_pliku
        self.stworz_tabele()

    def stworz_tabele(self):
        conn = sqlite3.connect(self.nazwa_pliku)
        c = conn.cursor()
        
        # Tabela zawiera teraz pola z Listy 3 (Value Boost)
        c.execute('''
            CREATE TABLE IF NOT EXISTS oferty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                platforma TEXT,
                tytul TEXT,
                cena INTEGER,
                
                -- Podstawowe
                marka TEXT, model TEXT, wersja TEXT, generacja TEXT,
                rocznik INTEGER, przebieg INTEGER, paliwo TEXT,
                pojemnosc INTEGER, moc INTEGER,
                nadwozie TEXT, kolor TEXT, skrzynia TEXT, naped TEXT,
                kraj TEXT, zarejestrowany TEXT, nr_rejestracyjny TEXT,
                
                -- Value Boost (Nowe)
                miasto TEXT, wojewodztwo TEXT, typ_sprzedawcy TEXT,
                liczba_zdjec INTEGER, liczba_opcji INTEGER,
                wyposazenie TEXT, opis TEXT,
                
                -- Systemowe
                zrodlo_aktualizacja TEXT,
                data_dodania TIMESTAMP,
                ostatnia_aktualizacja TIMESTAMP,
                first_seen TIMESTAMP, last_seen TIMESTAMP, is_active INTEGER DEFAULT 1
            )
        ''')
        
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
        conn.commit()
        conn.close()

    def upsert_oferta(self, dane):
        conn = sqlite3.connect(self.nazwa_pliku)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "ERROR"

        try:
            c.execute("SELECT id, cena FROM oferty WHERE url = ?", (dane['url'],))
            row = c.fetchone()

            if row is None:
                # INSERT z nowymi polami
                c.execute('''
                    INSERT INTO oferty (
                        url, platforma, tytul, cena, przebieg, rocznik,
                        marka, model, wersja, generacja, paliwo, pojemnosc, moc,
                        nadwozie, kolor, skrzynia, naped, kraj, zarejestrowany, nr_rejestracyjny,
                        miasto, wojewodztwo, typ_sprzedawcy, liczba_zdjec, liczba_opcji, wyposazenie, opis,
                        zrodlo_aktualizacja, data_dodania, ostatnia_aktualizacja, first_seen, last_seen, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    dane.get('url'), dane.get('platforma'), dane.get('tytul'), dane.get('cena'), 
                    dane.get('przebieg'), dane.get('rocznik'),
                    dane.get('marka'), dane.get('model'), dane.get('wersja'), dane.get('generacja'),
                    dane.get('paliwo'), dane.get('pojemnosc'), dane.get('moc'),
                    dane.get('nadwozie'), dane.get('kolor'), dane.get('skrzynia'), dane.get('naped'),
                    dane.get('kraj'), dane.get('zarejestrowany'), dane.get('nr_rejestracyjny'),
                    # Nowe pola
                    dane.get('miasto'), dane.get('wojewodztwo'), dane.get('typ_sprzedawcy'),
                    dane.get('liczba_zdjec'), dane.get('liczba_opcji'), dane.get('wyposazenie'), dane.get('opis'),
                    # Systemowe
                    dane.get('zrodlo_aktualizacja', ''), now, now, now, now
                ))
                new_id = c.lastrowid
                c.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                          (new_id, dane.get('cena'), dane.get('przebieg'), now))
                status = "INSERT"
            else:
                db_id, old_cena = row
                c.execute("UPDATE oferty SET last_seen = ?, is_active = 1 WHERE id = ?", (now, db_id))
                status = "SEEN"

                if old_cena != dane['cena']:
                    c.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                              (db_id, dane['cena'], dane['przebieg'], now))
                    status = "UPDATE_PRICE"

                # UPDATE z nowymi polami (zeby uzupelnic braki w starych rekordach)
                c.execute('''
                    UPDATE oferty SET 
                        cena = ?, przebieg = ?, rocznik = ?, tytul = ?,
                        miasto = ?, wojewodztwo = ?, typ_sprzedawcy = ?,
                        liczba_zdjec = ?, liczba_opcji = ?, wyposazenie = ?, opis = ?,
                        zrodlo_aktualizacja = ?, ostatnia_aktualizacja = ?
                    WHERE id = ?
                ''', (
                    dane['cena'], dane['przebieg'], dane['rocznik'], dane['tytul'],
                    dane.get('miasto'), dane.get('wojewodztwo'), dane.get('typ_sprzedawcy'),
                    dane.get('liczba_zdjec'), dane.get('liczba_opcji'), dane.get('wyposazenie'), dane.get('opis'),
                    dane.get('zrodlo_aktualizacja'), now, db_id
                ))

            conn.commit()
        except Exception as e:
            print(f"Blad SQL: {e}")
            status = "ERROR"
        finally:
            conn.close()
        return status

    def sprawdz_cene_przed_zmiana(self, url):
        conn = sqlite3.connect(self.nazwa_pliku)
        c = conn.cursor()
        c.execute("SELECT cena FROM oferty WHERE url = ?", (url,))
        wynik = c.fetchone()
        conn.close()
        return wynik[0] if wynik else None