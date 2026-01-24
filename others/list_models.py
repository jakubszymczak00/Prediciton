import sqlite3
import os
import datetime

DB_NAME = "baza_pojazdow.db"
OUTPUT_FILE = "raport_modeli_full.txt"

# Lista poprawnych modeli (z Twojego mappera) służąca do weryfikacji
VALID_MODELS = {
    "IVECO": ["DAILY", "EUROCARGO"],
    "FIAT": ["DUCATO", "DOBLO", "SCUDO", "FIORINO", "TALENTO"],
    "RENAULT": ["MASTER", "TRAFIC", "KANGOO", "CLIO", "MEGANE", "LAGUNA", "TALISMAN", "SCENIC", "ESPACE", "CAPTUR", "KADJAR"],
    "PEUGEOT": ["BOXER", "PARTNER", "EXPERT", "TRAVELLER", "RIFTER", "208", "308", "508", "2008", "3008", "5008"],
    "CITROEN": ["JUMPER", "BERLINGO", "JUMPY", "SPACETOURER", "C3", "C4", "C5"],
    "OPEL": ["MOVANO", "VIVARO", "COMBO", "ASTRA", "INSIGNIA", "CORSA", "ZAFIRA", "MOKKA", "CROSSLAND", "GRANDLAND"],
    "FORD": ["TRANSIT", "TRANSIT CUSTOM", "TRANSIT CONNECT", "TRANSIT COURIER", "RANGER", "FOCUS", "MONDEO", "FIESTA", "KUGA", "S-MAX", "GALAXY", "TOURNEO CUSTOM", "TOURNEO CONNECT", "TOURNEO COURIER"],
    "VOLKSWAGEN": ["TRANSPORTER", "CRAFTER", "CADDY", "AMAROK", "LT", "GOLF", "PASSAT", "POLO", "TIGUAN", "TOURAN", "SHARAN", "TOUAREG", "ARTEON", "T-ROC", "ID.3", "ID.4"],
    "MERCEDES-BENZ": ["SPRINTER", "VITO", "CITAN", "VIANO", "KLASA V", "KLASA A", "KLASA B", "KLASA C", "KLASA E", "KLASA S", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GLS", "KLASA G"],
    "TOYOTA": ["PROACE", "PROACE CITY", "PROACE MAX", "PROACE VERSO", "HILUX", "COROLLA", "YARIS", "RAV4", "AVENSIS", "AURIS", "C-HR", "HIGHLANDER", "LAND CRUISER", "PRIUS", "DYNA"],
    "BMW": ["SERIA 1", "SERIA 2", "SERIA 3", "SERIA 4", "SERIA 5", "SERIA 6", "SERIA 7", "SERIA 8", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Z4"],
    "AUDI": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "TT"],
    "SKODA": ["OCTAVIA", "SUPERB", "FABIA", "KODIAQ", "KAROQ", "KAMIQ", "SCALA", "RAPID"],
    "KIA": ["CEED", "SPORTAGE", "RIO", "SORENTO", "XCEED"],
    "HYUNDAI": ["I20", "I30", "TUCSON", "SANTA FE"],
    "VOLVO": ["XC60", "XC90", "S60", "V60", "V40"],
    "SEAT": ["IBIZA", "LEON", "ATECA", "ARONA"]
}

# Aliasy dla ułatwienia sprawdzania
VALID_MODELS["MERCEDES"] = VALID_MODELS["MERCEDES-BENZ"]
VALID_MODELS["VW"] = VALID_MODELS["VOLKSWAGEN"]

def analyze_models():
    if not os.path.exists(DB_NAME):
        print("Brak bazy danych.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Pobieramy dane: Marka, Model, Ilość, Min Rocznik, Max Rocznik
    query = """
        SELECT 
            UPPER(TRIM(marka)) as marka_clean, 
            TRIM(model) as model_clean, 
            COUNT(*),
            MIN(rocznik),
            MAX(rocznik)
        FROM oferty 
        WHERE is_active = 1
        GROUP BY UPPER(TRIM(marka)), UPPER(TRIM(model))
        ORDER BY marka_clean ASC, COUNT(*) DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("Brak danych.")
        return

    # Bufor do zapisu
    lines = []
    lines.append(f"RAPORT STANU MODELI - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("="*80)
    lines.append(f"{'STATUS':<4} | {'MARKA':<15} | {'MODEL (W BAZIE)':<30} | {'SZTUK':<5} | {'ROCZNIKI':<10}")
    lines.append("-" * 80)

    stats = {"ok": 0, "bad": 0}

    current_marka = ""
    
    for marka, model, count, min_rok, max_rok in rows:
        if not marka: marka = "BRAK MARKI"
        if not model: model = "BRAK MODELU"

        # Sprawdzamy czy model jest poprawny (zgodny z mapperem)
        is_valid = False
        if marka in VALID_MODELS:
            # Sprawdź czy model (dużymi literami) jest na liście
            if model.upper() in VALID_MODELS[marka]:
                is_valid = True
        
        # Oznaczenie graficzne
        if is_valid:
            status = "✅"
            stats["ok"] += count
        else:
            status = "❌"
            stats["bad"] += count

        # Nagłówek dla nowej marki
        if marka != current_marka:
            lines.append(f"\n--- {marka} ---")
            current_marka = marka

        # Linia raportu
        roczniki = f"{min_rok}-{max_rok}"
        lines.append(f"{status:<4} | {marka:<15} | {model:<30} | {count:<5} | {roczniki:<10}")

    # Podsumowanie
    lines.append("\n" + "="*80)
    lines.append(f"PODSUMOWANIE:")
    lines.append(f"Poprawne modele (pasujące do mappera): {stats['ok']}")
    lines.append(f"Nieznane / Śmieci (do poprawy):       {stats['bad']}")
    lines.append("="*80)
    lines.append("Jeśli widzisz ❌ przy modelu, który wygląda poprawnie (np. 'Proace ' ze spacją),")
    lines.append("oznacza to, że trzeba go wyczyścić w bazie lub dodać do listy VALID_MODELS.")

    # Zapis do pliku
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Raport wygenerowano w pliku: {OUTPUT_FILE}")
    print(f"Otwórz ten plik, aby zobaczyć, co trzeba jeszcze naprawić.")

if __name__ == "__main__":
    analyze_models()