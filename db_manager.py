import sqlite3
from datetime import datetime

class BazaDanych:
    def __init__(self, nazwa_pliku="baza_pojazdow.db"):
        self.nazwa_pliku = nazwa_pliku
        self.stworz_tabele()

    def stworz_tabele(self):
        conn = sqlite3.connect(self.nazwa_pliku)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS oferty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                platforma TEXT,
                tytul TEXT,
                cena INTEGER,
                marka TEXT,
                model TEXT,
                wersja TEXT,
                generacja TEXT,
                rocznik INTEGER,
                przebieg INTEGER,
                paliwo TEXT,
                pojemnosc INTEGER,
                moc INTEGER,
                nadwozie TEXT,
                kolor TEXT,
                skrzynia TEXT,
                naped TEXT,
                kraj TEXT,
                zarejestrowany TEXT,
                nr_rejestracyjny TEXT,
                zrodlo_aktualizacja TEXT,
                data_dodania TIMESTAMP,
                ostatnia_aktualizacja TIMESTAMP,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Tabela historii cen
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
            # Sprawdzenie czy oferta istnieje
            c.execute("SELECT id, cena FROM oferty WHERE url = ?", (dane['url'],))
            row = c.fetchone()

            if row is None:
                # Nowa oferta
                c.execute('''
                    INSERT INTO oferty (
                        url, platforma, tytul, cena, przebieg, rocznik,
                        marka, model, wersja, generacja, paliwo, pojemnosc, moc,
                        nadwozie, kolor, skrzynia, naped, kraj, zarejestrowany, nr_rejestracyjny,
                        zrodlo_aktualizacja, data_dodania, ostatnia_aktualizacja, 
                        first_seen, last_seen, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    dane.get('url'), dane.get('platforma'), dane.get('tytul'), dane.get('cena'), 
                    dane.get('przebieg'), dane.get('rocznik'),
                    dane.get('marka'), dane.get('model'), dane.get('wersja'), dane.get('generacja'),
                    dane.get('paliwo'), dane.get('pojemnosc'), dane.get('moc'),
                    dane.get('nadwozie'), dane.get('kolor'), dane.get('skrzynia'), dane.get('naped'),
                    dane.get('kraj'), dane.get('zarejestrowany'), dane.get('nr_rejestracyjny'),
                    dane.get('zrodlo_aktualizacja', ''), 
                    now, now, now, now
                ))
                new_id = c.lastrowid
                c.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                          (new_id, dane.get('cena'), dane.get('przebieg'), now))
                status = "INSERT"
            else:
                # Oferta istnieje
                db_id, old_cena = row
                c.execute("UPDATE oferty SET last_seen = ?, is_active = 1 WHERE id = ?", (now, db_id))
                status = "SEEN"

                # Aktualizacja pelnych danych i historii
                if old_cena != dane['cena']:
                    c.execute("INSERT INTO historia_cen (oferta_id, cena, przebieg, data_zmiany) VALUES (?, ?, ?, ?)",
                              (db_id, dane['cena'], dane['przebieg'], now))
                    status = "UPDATE_PRICE"

                # Zawsze aktualizujemy metadane
                c.execute('''
                    UPDATE oferty SET 
                        cena = ?, przebieg = ?, rocznik = ?, tytul = ?,
                        zrodlo_aktualizacja = ?, ostatnia_aktualizacja = ?
                    WHERE id = ?
                ''', (dane['cena'], dane['przebieg'], dane['rocznik'], dane['tytul'], 
                      dane.get('zrodlo_aktualizacja'), now, db_id))

            conn.commit()
        except Exception as e:
            print(f"Blad SQL: {e}")
            status = "ERROR"
        finally:
            conn.close()
        return status