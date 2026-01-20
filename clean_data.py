import sqlite3
import pandas as pd
import numpy as np

DB_NAME = "baza_pojazdow.db"

def usun_anomalie():
    print("Rozpoczynam czyszczenie bazy danych...")
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Pobieramy dane do analizy
    df = pd.read_sql_query("SELECT id, marka, model, cena, rocznik FROM oferty", conn)
    poczatkowa_ilosc = len(df)
    ids_to_delete = []

    #ETAP 1: Filtry Globalne (Oczywiste błędy)
    # Usuwamy auta tańsze niż 1000 zł (złom/błędy) i droższe niż 3 mln (zazwyczaj błędy lub unikaty psujące statystykę)
    smieci = df[ (df['cena'] < 1500) | (df['cena'] > 1000000) ]
    ids_to_delete.extend(smieci['id'].tolist())
    print(f"Znaleziono {len(smieci)} ofert z ceną nierealną (< 1.5k lub > 1mln).")

    #ETAP 2: Filtry Kontekstowe (Per Model)
    # To jest "Big Data Approach". Golf za 300k to błąd. Porsche za 300k to norma.
    # Używamy metody: Usuń oferty, które są 3x droższe niż średnia dla tego modelu i rocznika.
    
    print("Analizuję ceny w kontekście modeli...")
    
    # Grupujemy po Modelu (żeby nie porównywać Fiata z BMW)
    # Obliczamy średnią cenę dla każdego modelu
    statystyki = df.groupby('model')['cena'].agg(['mean', 'std']).reset_index()
    
    # Dołączamy statystyki do głównej tabeli
    df = df.merge(statystyki, on='model')
    
    # Wykrywamy anomalie: Cena > Średnia + 3 * OdchylenieStandardowe (Z-Score > 3)
    # To statystyczna definicja "skrajnej wartości"
    
    # Zabezpieczenie: jeśli std jest NaN (pojedyncze auto), przyjmujemy 0
    df['std'].fillna(0, inplace=True)
    
    anomalie = df[ df['cena'] > (df['mean'] + 3 * df['std']) ]
    
    # Dodatkowe zabezpieczenie: nie usuwamy, jeśli to jedyne auto tego typu
    anomalie = anomalie[ anomalie['std'] > 0 ] 
    
    ids_to_delete.extend(anomalie['id'].tolist())
    print(f"Znaleziono {len(anomalie)} statystycznych anomalii cenowych (np. Golf za milion).")

    #ETAP 3: Usuwanie z Bazy (Commit)
    ids_to_delete = list(set(ids_to_delete)) # Usuwamy duplikaty ID
    
    if ids_to_delete:
        print(f"Usuwam łącznie {len(ids_to_delete)} rekordów z bazy...")
        
        # SQL nie lubi listy [1, 2, 3], trzeba ją zamienić na string "(1, 2, 3)"
        ids_tuple = tuple(ids_to_delete)
        
        # Jeśli tylko 1 element, tuple dodaje przecinek (1,), co SQL może źle zinterpretować w IN,
        # ale zazwyczaj Python driver to ogarnia. Dla pewności przy dużej liście:
        chunk_size = 1000
        cursor = conn.cursor()
        
        for i in range(0, len(ids_to_delete), chunk_size):
            chunk = ids_to_delete[i:i + chunk_size]
            query = f"DELETE FROM oferty WHERE id IN ({','.join(map(str, chunk))})"
            cursor.execute(query)
            
        conn.commit()
        print("Baza wyczyszczona.")
    else:
        print("Baza jest czysta, nie znaleziono anomalii.")
        
    koncowa_ilosc = poczatkowa_ilosc - len(ids_to_delete)
    print(f"Statystyka: {poczatkowa_ilosc} -> {koncowa_ilosc} ofert.")
    conn.close()

if __name__ == "__main__":
    usun_anomalie()