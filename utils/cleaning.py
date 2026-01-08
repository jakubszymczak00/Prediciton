import re

def clean_int(val):
    # Czysci wartosc tekstowa do liczby calkowitej
    # Usuwa spacje, jednostki, bierze pierwsza napotkana liczbe
    if not val:
        return None
    
    try:
        # Zamiana na string i usuniecie bialych znakow
        val_str = str(val).replace(" ", "").replace("\xa0", "")
        
        # Szukanie ciagu cyfr
        match = re.search(r'(\d+)', val_str)
        
        if match:
            liczba = int(match.group(1))
            
            # Filtr bezpieczenstwa dla zbyt duzych liczb (bledy parsowania)
            if liczba > 20000000:
                return None
                
            return liczba
            
        return None
    except:
        return None