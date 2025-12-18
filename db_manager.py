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
                ostatnia_aktualizacja TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def upsert_oferta(self, dane):
        conn = sqlite3.connect(self.nazwa_pliku)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Zapytanie UPSERT - Jeśli link istnieje, aktualizujemy WSZYSTKIE pola
            # Dzięki temu, jeśli sprzedawca zmieni przebieg, opis czy rocznik, 
            # my też to zaktualizujemy w bazie.
            
            c.execute('''
                INSERT INTO oferty (
                    url, platforma, tytul, cena, zrodlo_aktualizacja,
                    marka, model, wersja, generacja, rocznik, przebieg, paliwo,
                    pojemnosc, moc, nadwozie, kolor, skrzynia, naped,
                    kraj, zarejestrowany, nr_rejestracyjny,
                    data_dodania, ostatnia_aktualizacja
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    cena = excluded.cena,
                    tytul = excluded.tytul,
                    zrodlo_aktualizacja = excluded.zrodlo_aktualizacja,
                    
                    marka = excluded.marka,
                    model = excluded.model,
                    wersja = excluded.wersja,
                    generacja = excluded.generacja,
                    rocznik = excluded.rocznik,
                    przebieg = excluded.przebieg,
                    paliwo = excluded.paliwo,
                    pojemnosc = excluded.pojemnosc,
                    moc = excluded.moc,
                    nadwozie = excluded.nadwozie,
                    kolor = excluded.kolor,
                    skrzynia = excluded.skrzynia,
                    naped = excluded.naped,
                    kraj = excluded.kraj,
                    zarejestrowany = excluded.zarejestrowany,
                    nr_rejestracyjny = excluded.nr_rejestracyjny,
                    
                    ostatnia_aktualizacja = excluded.ostatnia_aktualizacja
            ''', (
                dane.get('url'),
                dane.get('platforma'),
                dane.get('tytul'),
                dane.get('cena'),
                dane.get('zrodlo_aktualizacja', ''),
                
                dane.get('marka'),
                dane.get('model'),
                dane.get('wersja'),
                dane.get('generacja'),
                dane.get('rocznik'),
                dane.get('przebieg'),
                dane.get('paliwo'),
                dane.get('pojemnosc'),
                dane.get('moc'),
                dane.get('nadwozie'),
                dane.get('kolor'),
                dane.get('skrzynia'),
                dane.get('naped'),
                dane.get('kraj'),
                dane.get('zarejestrowany'),
                dane.get('nr_rejestracyjny'),
                
                now, # data_dodania (tylko przy nowym)
                now  # ostatnia_aktualizacja (zawsze aktualizowana)
            ))
            conn.commit()
            status = "OK"
        except Exception as e:
            print(f"Błąd SQL: {e}")
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