import sqlite3
import re

from utils.mapper import MODELS_DB

DB_NAME = "baza_pojazdow.db"


aliasy_marek = {
    "MERCEDES": "MERCEDES-BENZ",
    "VW": "VOLKSWAGEN"
}

def get_clean_model_v3(marka_raw, model_raw):
    if not model_raw or not marka_raw:
        return None

    # Normalizacja
    marka_upper = marka_raw.upper().strip()
    model_upper = str(model_raw).upper().strip()
    

    if marka_upper in aliasy_marek:
        marka_upper = aliasy_marek[marka_upper]


    
    # IVECO
    if "IVECO" in marka_upper:
        if "EUROCARGO" in model_upper: return "EUROCARGO"
        if re.match(r'^\d', model_upper) or "35S" in model_upper or "50C" in model_upper or "AG" in model_upper:
            return "DAILY"

    # FORD
    if "FORD" in marka_upper:
        if any(x in model_upper for x in ["BENIMAR", "RIMOR", "CHAUSSON"]):
            return "TRANSIT" 
        if "RAPTOR" in model_upper and "RANGER" not in model_upper:
            return "RANGER"

    # TOYOTA
    if "TOYOTA" in marka_upper:
        if "HILUX" in model_upper: return "HILUX"
        if "DYNA" in model_upper: return "DYNA"

    # MERCEDES
    if "MERCEDES" in marka_upper:
        if model_upper == "ML": return "GLE"
        match = re.search(r'(KLASA\s+[A-Z]|V-KLASA|[A-Z]-KLASA)', model_upper)
        if match:
            letter = match.group(0).replace("KLASA", "").replace("-", "").strip()
            return f"KLASA {letter}"

    # AUDI
    if "AUDI" in marka_upper:
        if re.match(r'^S\d', model_upper): return "A" + model_upper[1]
        if re.match(r'^RS\d', model_upper): return "A" + model_upper[2]


    
    if marka_upper in MODELS_DB:
       
        mozliwe_modele = sorted(MODELS_DB[marka_upper].keys(), key=len, reverse=True)
        
        for poprawny_model in mozliwe_modele:
            if poprawny_model in model_upper:
                return poprawny_model
                

    cleaned = model_upper.replace(marka_upper, "").strip()
    cleaned = re.sub(r'\b20\d{2}R?\b', '', cleaned)
    cleaned = re.sub(r'[^A-Z0-9\s]', '', cleaned).strip()
    
    if marka_upper in MODELS_DB:
        for poprawny_model in MODELS_DB[marka_upper]:
            if cleaned == poprawny_model:
                return poprawny_model

    return None

def execute_cleaning():
    print("--- ROZPOCZYNAM CZYSZCZENIE MODELI V3 (W oparciu o Mapper) ---")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, marka, model FROM oferty WHERE model IS NOT NULL")
    rows = cursor.fetchall()
    
    batch_updates = []
    
    for row in rows:
        db_id, marka, raw_model = row
        clean_model = get_clean_model_v3(marka, raw_model)
        
        if clean_model and clean_model != raw_model:
            # Normalizacja wielkości liter
            clean_model_title = clean_model.title()
            if "Klasa" in clean_model_title:
                 parts = clean_model.split()
                 if len(parts) > 1: clean_model_title = f"Klasa {parts[1]}"
            elif clean_model == "RAV4": clean_model_title = "RAV4"
            elif clean_model == "C-HR": clean_model_title = "C-HR"
            
            batch_updates.append((clean_model_title, db_id))
    
    if batch_updates:
        print(f"\nZapisuję {len(batch_updates)} zmian...")
        cursor.executemany("UPDATE oferty SET model = ? WHERE id = ?", batch_updates)
        conn.commit()
        print("Gotowe.")
    else:
        print("Brak zmian.")
        
    conn.close()

if __name__ == "__main__":
    execute_cleaning()