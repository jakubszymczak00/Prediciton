# Konfiguracja filtrowania
ROK_OD = 2017
TYLKO_NIEUSZKODZONE = True

# Slownik marek i modeli
# Struktura: ID -> Marka -> Modele -> ID -> {nazwa, slug_oto, slug_auto}
# Dodalem rozróznienie slugow, bo Otomoto i Autoplac moga miec inne (np. a-klasa vs klasa-a)
SAMOCHODY = {
    "1": {
        "marka": "bmw", 
        "nazwa": "BMW",
        "modele": {
            "1": {"nazwa": "Seria 1", "slug_oto": "seria-1", "slug_auto": "seria-1"},
            "2": {"nazwa": "Seria 3", "slug_oto": "seria-3", "slug_auto": "seria-3"},
            "3": {"nazwa": "Seria 4", "slug_oto": "seria-4", "slug_auto": "seria-4"},
            "4": {"nazwa": "Seria 5", "slug_oto": "seria-5", "slug_auto": "seria-5"},
            "5": {"nazwa": "Seria 7", "slug_oto": "seria-7", "slug_auto": "seria-7"},
            "6": {"nazwa": "X1", "slug_oto": "x1", "slug_auto": "x1"},
            "7": {"nazwa": "X3", "slug_oto": "x3", "slug_auto": "x3"},
            "8": {"nazwa": "X5", "slug_oto": "x5", "slug_auto": "x5"},
            "9": {"nazwa": "X6", "slug_oto": "x6", "slug_auto": "x6"}
        }
    },
    "2": {
        "marka": "audi", 
        "nazwa": "Audi",
        "modele": {
            "1": {"nazwa": "A3", "slug_oto": "a3", "slug_auto": "a3"},
            "2": {"nazwa": "A4", "slug_oto": "a4", "slug_auto": "a4"},
            "3": {"nazwa": "A6", "slug_oto": "a6", "slug_auto": "a6"},
            "4": {"nazwa": "Q5", "slug_oto": "q5", "slug_auto": "q5"},
            "5": {"nazwa": "Q7", "slug_oto": "q7", "slug_auto": "q7"}
        }
    },
    "3": {
        "marka": "mercedes-benz", 
        "nazwa": "Mercedes-Benz",
        "modele": {
            # Uwaga: Otomoto uzywa a-klasa, Autoplac czesto tez lub klasa-a
            # Tutaj wpisz poprawne slugi dla kazdej platformy
            "1": {"nazwa": "Klasa A", "slug_oto": "a-klasa", "slug_auto": "klasa-a"},
            "2": {"nazwa": "Klasa C", "slug_oto": "c-klasa", "slug_auto": "klasa-c"},
            "3": {"nazwa": "Klasa E", "slug_oto": "e-klasa", "slug_auto": "klasa-e"},
            "4": {"nazwa": "GLE", "slug_oto": "gle", "slug_auto": "gle"}
        }
    },
    "4": {
        "marka": "skoda", 
        "nazwa": "Skoda",
        "modele": {

            "1": {"nazwa": "Kamiq", "slug_oto": "kamiq", "slug_auto": "kamiq"},
            "2": {"nazwa": "Karoq", "slug_oto": "karoq", "slug_auto": "karoq"},
            "3": {"nazwa": "Kodiaq", "slug_oto": "kodiaq", "slug_auto": "kodiaq"},
            "4": {"nazwa": "Octavia", "slug_oto": "octavia", "slug_auto": "octavia"},
            "5": {"nazwa": "Scala", "slug_oto": "scala", "slug_auto": "scala"},
            "6": {"nazwa": "Superb", "slug_oto": "superb", "slug_auto": "superb"},
            "7": {"nazwa": "Fabia", "slug_oto": "fabia", "slug_auto": "fabia"},
            "8": {"nazwa": "Enyaq", "slug_oto": "enyaq", "slug_auto": "enyaq"},
            "9": {"nazwa": "Roomster", "slug_oto": "roomster", "slug_auto": "roomster"}
        }
    },
    "5": {
    "marka": "honda", 
    "nazwa": "Honda",
    "modele": {

        "1": {"nazwa": "Accord", "slug_oto": "accord", "slug_auto": "accord"},
        "2": {"nazwa": "Civic", "slug_oto": "civic", "slug_auto": "civic"},
        "3": {"nazwa": "Kodiaq", "slug_oto": "kodiaq", "slug_auto": "kodiaq"},
        "4": {"nazwa": "CR-V", "slug_oto": "cr-v", "slug_auto": "cr-v"},
        "5": {"nazwa": "HR-V", "slug_oto": "hr-v", "slug_auto": "hr-v"},
        "6": {"nazwa": "ZR-V", "slug_oto": "zr-v", "slug_auto": "zr-v"},
        "7": {"nazwa": "Odyssey", "slug_oto": "odyssey", "slug_auto": "odyssey"},
        "8": {"nazwa": "Jazz", "slug_oto": "jazz", "slug_auto": "jazz"}
    }
}
    
}