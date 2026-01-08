import time
from functools import wraps

def retry(max_retries=3, delay=2):
    # Dekorator do ponawiania proby wykonania funkcji w razie bledu
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    # Wypisujemy info o bledzie
                    print(f" [Blad sieci] Proba {attempt}/{max_retries}. Czekam {delay}s...")
                    time.sleep(delay)
            
            # Jesli po wszystkich probach dalej blad
            print(f" [Krytyczny] Nie udalo sie pobrac danych: {last_exception}")
            return None
        return wrapper
    return decorator