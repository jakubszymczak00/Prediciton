# utils/config.py

# --- USTAWIENIA GLOBALNE ---
ROK_OD_OSOBOWE = 2017
ROK_OD_DOSTAWCZE = 2012
TYLKO_NIEUSZKODZONE = True

# ==========================================
#          SAMOCHODY DOSTAWCZE
# ==========================================
DOSTAWCZE = {
    "1": {
        "nazwa": "IVECO",
        "marka": "iveco",
        "modele": {
            "1": {"nazwa": "Daily", "slug_oto": "daily", "slug_auto": "daily"}
        }
    },
    "2": {
        "nazwa": "FIAT",
        "marka": "fiat",
        "modele": {
            "1": {"nazwa": "Ducato", "slug_oto": "ducato", "slug_auto": "ducato"},
            "2": {"nazwa": "Doblo", "slug_oto": "doblo", "slug_auto": "doblo"},
            "3": {"nazwa": "Fiorino", "slug_oto": "fiorino", "slug_auto": "fiorino"},
            "4": {"nazwa": "Scudo", "slug_oto": "scudo", "slug_auto": "scudo"},
            "5": {"nazwa": "Talento", "slug_oto": "talento", "slug_auto": "talento"}
        }
    },
    "3": {
        "nazwa": "RENAULT",
        "marka": "renault",
        "modele": {
            "1": {"nazwa": "Master", "slug_oto": "master", "slug_auto": "master"},
            "2": {"nazwa": "Trafic", "slug_oto": "trafic", "slug_auto": "trafic"},
            "3": {"nazwa": "Kangoo", "slug_oto": "kangoo", "slug_auto": "kangoo"}
        }
    },
    "4": {
        "nazwa": "MERCEDES-BENZ",
        "marka": "mercedes-benz",
        "modele": {
            "1": {"nazwa": "Sprinter", "slug_oto": "sprinter", "slug_auto": "sprinter"},
            "2": {"nazwa": "Vito", "slug_oto": "vito", "slug_auto": "vito"},
            "3": {"nazwa": "Citan", "slug_oto": "citan", "slug_auto": "citan"}
        }
    },
    "5": {
        "nazwa": "VOLKSWAGEN",
        "marka": "volkswagen",
        "modele": {
            "1": {"nazwa": "Transporter", "slug_oto": "transporter", "slug_auto": "transporter"},
            "2": {"nazwa": "Crafter", "slug_oto": "crafter", "slug_auto": "crafter"},
            "3": {"nazwa": "Caddy", "slug_oto": "caddy", "slug_auto": "caddy"},
            "4": {"nazwa": "Amarok", "slug_oto": "amarok", "slug_auto": "amarok"},
            "5": {"nazwa": "LT", "slug_oto": "lt", "slug_auto": "lt"}
        }
    },
    "6": {
        "nazwa": "FORD",
        "marka": "ford",
        "modele": {
            "1": {"nazwa": "Transit", "slug_oto": "transit", "slug_auto": "transit"},
            "2": {"nazwa": "Transit Custom", "slug_oto": "transit-custom", "slug_auto": "transit-custom"},
            "3": {"nazwa": "Transit Connect", "slug_oto": "transit-connect", "slug_auto": "transit-connect"},
            "4": {"nazwa": "Ranger", "slug_oto": "ranger", "slug_auto": "ranger"}
        }
    },
    "7": {
        "nazwa": "PEUGEOT",
        "marka": "peugeot",
        "modele": {
            "1": {"nazwa": "Boxer", "slug_oto": "boxer", "slug_auto": "boxer"},
            "2": {"nazwa": "Partner", "slug_oto": "partner", "slug_auto": "partner"},
            "3": {"nazwa": "Expert", "slug_oto": "expert", "slug_auto": "expert"},
            "4": {"nazwa": "Rifter", "slug_oto": "rifter", "slug_auto": "rifter"},
            "5": {"nazwa": "Traveller", "slug_oto": "traveller", "slug_auto": "traveller"}
        }
    },
    "8": {
        "nazwa": "CITROEN",
        "marka": "citroen",
        "modele": {
            "1": {"nazwa": "Jumper", "slug_oto": "jumper", "slug_auto": "jumper"},
            "2": {"nazwa": "Berlingo", "slug_oto": "berlingo", "slug_auto": "berlingo"},
            "3": {"nazwa": "Jumpy", "slug_oto": "jumpy", "slug_auto": "jumpy"},
            "4": {"nazwa": "Spacetourer", "slug_oto": "spacetourer", "slug_auto": "spacetourer"}
        }
    },
    "9": {
        "nazwa": "OPEL",
        "marka": "opel",
        "modele": {
            "1": {"nazwa": "Movano", "slug_oto": "movano", "slug_auto": "movano"},
            "2": {"nazwa": "Vivaro", "slug_oto": "vivaro", "slug_auto": "vivaro"},
            "3": {"nazwa": "Combo", "slug_oto": "combo", "slug_auto": "combo"}
        }
    },
    "10": {
        "nazwa": "TOYOTA",
        "marka": "toyota",
        "modele": {
            "1": {"nazwa": "Proace", "slug_oto": "proace", "slug_auto": "proace"},
            "2": {"nazwa": "Hilux", "slug_oto": "hilux", "slug_auto": "hilux"}
        }
    }
}

# ==========================================
#           SAMOCHODY OSOBOWE
# ==========================================
SAMOCHODY = {
    "1": {
        "nazwa": "BMW",
        "marka": "bmw",
        "modele": {
            "1": {"nazwa": "Seria 3", "slug_oto": "seria-3", "slug_auto": "seria-3"},
            "2": {"nazwa": "Seria 5", "slug_oto": "seria-5", "slug_auto": "seria-5"},
            "3": {"nazwa": "Seria 1", "slug_oto": "seria-1", "slug_auto": "seria-1"},
            "4": {"nazwa": "Seria 2", "slug_oto": "seria-2", "slug_auto": "seria-2"},
            "5": {"nazwa": "Seria 4", "slug_oto": "seria-4", "slug_auto": "seria-4"},
            "6": {"nazwa": "Seria 7", "slug_oto": "seria-7", "slug_auto": "seria-7"},
            "7": {"nazwa": "X1", "slug_oto": "x1", "slug_auto": "x1"},
            "8": {"nazwa": "X3", "slug_oto": "x3", "slug_auto": "x3"},
            "9": {"nazwa": "X5", "slug_oto": "x5", "slug_auto": "x5"},
            "10": {"nazwa": "X6", "slug_oto": "x6", "slug_auto": "x6"}
        }
    },
    "2": {
        "nazwa": "AUDI",
        "marka": "audi",
        "modele": {
            "1": {"nazwa": "A3", "slug_oto": "a3", "slug_auto": "a3"},
            "2": {"nazwa": "A4", "slug_oto": "a4", "slug_auto": "a4"},
            "3": {"nazwa": "A5", "slug_oto": "a5", "slug_auto": "a5"},
            "4": {"nazwa": "A6", "slug_oto": "a6", "slug_auto": "a6"},
            "5": {"nazwa": "A7", "slug_oto": "a7", "slug_auto": "a7"},
            "6": {"nazwa": "A8", "slug_oto": "a8", "slug_auto": "a8"},
            "7": {"nazwa": "Q3", "slug_oto": "q3", "slug_auto": "q3"},
            "8": {"nazwa": "Q5", "slug_oto": "q5", "slug_auto": "q5"},
            "9": {"nazwa": "Q7", "slug_oto": "q7", "slug_auto": "q7"},
            "10": {"nazwa": "Q8", "slug_oto": "q8", "slug_auto": "q8"}
        }
    },
    "3": {
        "nazwa": "MERCEDES-BENZ",
        "marka": "mercedes-benz",
        "modele": {
            "1": {"nazwa": "Klasa A", "slug_oto": "klasa-a", "slug_auto": "klasa-a"},
            "2": {"nazwa": "Klasa C", "slug_oto": "klasa-c", "slug_auto": "klasa-c"},
            "3": {"nazwa": "Klasa E", "slug_oto": "klasa-e", "slug_auto": "klasa-e"},
            "4": {"nazwa": "Klasa S", "slug_oto": "klasa-s", "slug_auto": "klasa-s"},
            "5": {"nazwa": "CLA", "slug_oto": "cla", "slug_auto": "cla"},
            "6": {"nazwa": "CLS", "slug_oto": "cls", "slug_auto": "cls"},
            "7": {"nazwa": "GLA", "slug_oto": "gla", "slug_auto": "gla"},
            "8": {"nazwa": "GLC", "slug_oto": "glc", "slug_auto": "glc"},
            "9": {"nazwa": "GLE", "slug_oto": "gle", "slug_auto": "gle"},
            "10": {"nazwa": "GLS", "slug_oto": "gls", "slug_auto": "gls"}
        }
    },
    "4": {
        "nazwa": "VOLKSWAGEN",
        "marka": "volkswagen",
        "modele": {
            "1": {"nazwa": "Golf", "slug_oto": "golf", "slug_auto": "golf"},
            "2": {"nazwa": "Passat", "slug_oto": "passat", "slug_auto": "passat"},
            "3": {"nazwa": "Polo", "slug_oto": "polo", "slug_auto": "polo"},
            "4": {"nazwa": "Tiguan", "slug_oto": "tiguan", "slug_auto": "tiguan"},
            "5": {"nazwa": "Touran", "slug_oto": "touran", "slug_auto": "touran"},
            "6": {"nazwa": "Touareg", "slug_oto": "touareg", "slug_auto": "touareg"},
            "7": {"nazwa": "Arteon", "slug_oto": "arteon", "slug_auto": "arteon"},
            "8": {"nazwa": "T-Roc", "slug_oto": "t-roc", "slug_auto": "t-roc"},
            "9": {"nazwa": "ID.3", "slug_oto": "id-3", "slug_auto": "id-3"},
            "10": {"nazwa": "ID.4", "slug_oto": "id-4", "slug_auto": "id-4"}
        }
    },
    "5": {
        "nazwa": "TOYOTA",
        "marka": "toyota",
        "modele": {
            "1": {"nazwa": "Corolla", "slug_oto": "corolla", "slug_auto": "corolla"},
            "2": {"nazwa": "Yaris", "slug_oto": "yaris", "slug_auto": "yaris"},
            "3": {"nazwa": "Auris", "slug_oto": "auris", "slug_auto": "auris"},
            "4": {"nazwa": "Avensis", "slug_oto": "avensis", "slug_auto": "avensis"},
            "5": {"nazwa": "RAV4", "slug_oto": "rav4", "slug_auto": "rav4"},
            "6": {"nazwa": "C-HR", "slug_oto": "c-hr", "slug_auto": "c-hr"},
            "7": {"nazwa": "Highlander", "slug_oto": "highlander", "slug_auto": "highlander"},
            "8": {"nazwa": "Land Cruiser", "slug_oto": "land-cruiser", "slug_auto": "land-cruiser"}
        }
    },
    "6": {
        "nazwa": "FORD",
        "marka": "ford",
        "modele": {
            "1": {"nazwa": "Focus", "slug_oto": "focus", "slug_auto": "focus"},
            "2": {"nazwa": "Mondeo", "slug_oto": "mondeo", "slug_auto": "mondeo"},
            "3": {"nazwa": "Fiesta", "slug_oto": "fiesta", "slug_auto": "fiesta"},
            "4": {"nazwa": "Kuga", "slug_oto": "kuga", "slug_auto": "kuga"},
            "5": {"nazwa": "S-Max", "slug_oto": "s-max", "slug_auto": "s-max"},
            "6": {"nazwa": "Galaxy", "slug_oto": "galaxy", "slug_auto": "galaxy"}
        }
    },
    "7": {
        "nazwa": "SKODA",
        "marka": "skoda",
        "modele": {
            "1": {"nazwa": "Octavia", "slug_oto": "octavia", "slug_auto": "octavia"},
            "2": {"nazwa": "Superb", "slug_oto": "superb", "slug_auto": "superb"},
            "3": {"nazwa": "Fabia", "slug_oto": "fabia", "slug_auto": "fabia"},
            "4": {"nazwa": "Kodiaq", "slug_oto": "kodiaq", "slug_auto": "kodiaq"},
            "5": {"nazwa": "Karoq", "slug_oto": "karoq", "slug_auto": "karoq"},
            "6": {"nazwa": "Kamiq", "slug_oto": "kamiq", "slug_auto": "kamiq"},
            "7": {"nazwa": "Scala", "slug_oto": "scala", "slug_auto": "scala"}
        }
    },
    "8": {
        "nazwa": "OPEL",
        "marka": "opel",
        "modele": {
            "1": {"nazwa": "Astra", "slug_oto": "astra", "slug_auto": "astra"},
            "2": {"nazwa": "Insignia", "slug_oto": "insignia", "slug_auto": "insignia"},
            "3": {"nazwa": "Corsa", "slug_oto": "corsa", "slug_auto": "corsa"},
            "4": {"nazwa": "Mokka", "slug_oto": "mokka", "slug_auto": "mokka"},
            "5": {"nazwa": "Zafira", "slug_oto": "zafira", "slug_auto": "zafira"},
            "6": {"nazwa": "Crossland", "slug_oto": "crossland", "slug_auto": "crossland"},
            "7": {"nazwa": "Grandland", "slug_oto": "grandland", "slug_auto": "grandland"}
        }
    },
    "9": {
        "nazwa": "RENAULT",
        "marka": "renault",
        "modele": {
            "1": {"nazwa": "Clio", "slug_oto": "clio", "slug_auto": "clio"},
            "2": {"nazwa": "Megane", "slug_oto": "megane", "slug_auto": "megane"},
            "3": {"nazwa": "Laguna", "slug_oto": "laguna", "slug_auto": "laguna"},
            "4": {"nazwa": "Talisman", "slug_oto": "talisman", "slug_auto": "talisman"},
            "5": {"nazwa": "Captur", "slug_oto": "captur", "slug_auto": "captur"},
            "6": {"nazwa": "Kadjar", "slug_oto": "kadjar", "slug_auto": "kadjar"},
            "7": {"nazwa": "Scenic", "slug_oto": "scenic", "slug_auto": "scenic"},
            "8": {"nazwa": "Espace", "slug_oto": "espace", "slug_auto": "espace"}
        }
    },
    "10": {
        "nazwa": "PEUGEOT",
        "marka": "peugeot",
        "modele": {
            "1": {"nazwa": "208", "slug_oto": "208", "slug_auto": "208"},
            "2": {"nazwa": "308", "slug_oto": "308", "slug_auto": "308"},
            "3": {"nazwa": "508", "slug_oto": "508", "slug_auto": "508"},
            "4": {"nazwa": "2008", "slug_oto": "2008", "slug_auto": "2008"},
            "5": {"nazwa": "3008", "slug_oto": "3008", "slug_auto": "3008"},
            "6": {"nazwa": "5008", "slug_oto": "5008", "slug_auto": "5008"}
        }
    },
    "11": {
        "nazwa": "CITROEN",
        "marka": "citroen",
        "modele": {
            "1": {"nazwa": "C3", "slug_oto": "c3", "slug_auto": "c3"},
            "2": {"nazwa": "C4", "slug_oto": "c4", "slug_auto": "c4"},
            "3": {"nazwa": "C5", "slug_oto": "c5", "slug_auto": "c5"},
            "4": {"nazwa": "C5 Aircross", "slug_oto": "c5-aircross", "slug_auto": "c5-aircross"}
        }
    },
    "12": {
        "nazwa": "KIA",
        "marka": "kia",
        "modele": {
            "1": {"nazwa": "Ceed", "slug_oto": "ceed", "slug_auto": "ceed"},
            "2": {"nazwa": "Sportage", "slug_oto": "sportage", "slug_auto": "sportage"},
            "3": {"nazwa": "Rio", "slug_oto": "rio", "slug_auto": "rio"},
            "4": {"nazwa": "Sorento", "slug_oto": "sorento", "slug_auto": "sorento"},
            "5": {"nazwa": "Xceed", "slug_oto": "xceed", "slug_auto": "xceed"}
        }
    },
    "13": {
        "nazwa": "HYUNDAI",
        "marka": "hyundai",
        "modele": {
            "1": {"nazwa": "i20", "slug_oto": "i20", "slug_auto": "i20"},
            "2": {"nazwa": "i30", "slug_oto": "i30", "slug_auto": "i30"},
            "3": {"nazwa": "Tucson", "slug_oto": "tucson", "slug_auto": "tucson"},
            "4": {"nazwa": "Santa Fe", "slug_oto": "santa-fe", "slug_auto": "santa-fe"}
        }
    },
    "14": {
        "nazwa": "MAZDA",
        "marka": "mazda",
        "modele": {
            "1": {"nazwa": "2", "slug_oto": "2", "slug_auto": "2"},
            "2": {"nazwa": "3", "slug_oto": "3", "slug_auto": "3"},
            "3": {"nazwa": "6", "slug_oto": "6", "slug_auto": "6"},
            "4": {"nazwa": "CX-3", "slug_oto": "cx-3", "slug_auto": "cx-3"},
            "5": {"nazwa": "CX-5", "slug_oto": "cx-5", "slug_auto": "cx-5"},
            "6": {"nazwa": "CX-30", "slug_oto": "cx-30", "slug_auto": "cx-30"},
            "7": {"nazwa": "CX-60", "slug_oto": "cx-60", "slug_auto": "cx-60"}
        }
    },
    "15": {
        "nazwa": "HONDA",
        "marka": "honda",
        "modele": {
            "1": {"nazwa": "Civic", "slug_oto": "civic", "slug_auto": "civic"},
            "2": {"nazwa": "Accord", "slug_oto": "accord", "slug_auto": "accord"},
            "3": {"nazwa": "CR-V", "slug_oto": "cr-v", "slug_auto": "cr-v"},
            "4": {"nazwa": "HR-V", "slug_oto": "hr-v", "slug_auto": "hr-v"}
        }
    },
    "16": {
        "nazwa": "NISSAN",
        "marka": "nissan",
        "modele": {
            "1": {"nazwa": "Qashqai", "slug_oto": "qashqai", "slug_auto": "qashqai"},
            "2": {"nazwa": "Juke", "slug_oto": "juke", "slug_auto": "juke"},
            "3": {"nazwa": "X-Trail", "slug_oto": "x-trail", "slug_auto": "x-trail"},
            "4": {"nazwa": "Micra", "slug_oto": "micra", "slug_auto": "micra"}
        }
    },
    "17": {
        "nazwa": "VOLVO",
        "marka": "volvo",
        "modele": {
            "1": {"nazwa": "XC60", "slug_oto": "xc60", "slug_auto": "xc60"},
            "2": {"nazwa": "XC90", "slug_oto": "xc90", "slug_auto": "xc90"},
            "3": {"nazwa": "S60", "slug_oto": "s60", "slug_auto": "s60"},
            "4": {"nazwa": "V60", "slug_oto": "v60", "slug_auto": "v60"},
            "5": {"nazwa": "V40", "slug_oto": "v40", "slug_auto": "v40"}
        }
    },
    "18": {
        "nazwa": "SEAT",
        "marka": "seat",
        "modele": {
            "1": {"nazwa": "Ibiza", "slug_oto": "ibiza", "slug_auto": "ibiza"},
            "2": {"nazwa": "Leon", "slug_oto": "leon", "slug_auto": "leon"},
            "3": {"nazwa": "Ateca", "slug_oto": "ateca", "slug_auto": "ateca"},
            "4": {"nazwa": "Arona", "slug_oto": "arona", "slug_auto": "arona"}
        }
    }
}