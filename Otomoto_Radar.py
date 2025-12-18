import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

def main():
    print("=========================================")
    print("   🕵️‍♂️ OTOMOTO RADAR v2 (Interaktywny)   ")
    print("=========================================")
    
    # Tutaj program poprosi Cię o działający link
    url = input("\n👉 Wklej tutaj link do aktywnego ogłoszenia i naciśnij ENTER:\n").strip()
    
    if not url:
        print("❌ Nie podano linku!")
        return

    print(f"\n🚀 Otwieram przeglądarkę i jadę pod adres: {url[:50]}...")
    
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    driver = uc.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(3) # Czekamy aż strona się załaduje
        
        print("\n--- SKANOWANIE STRUKTURY HTML ---")
        
        # Lista parametrów, których szukamy
        szukane = ["Generacja", "Wersja", "Kolor", "Napęd", "Skrzynia biegów"]
        
        found_any = False

        for param in szukane:
            print(f"\n🔎 Szukam słowa: '{param}'...")
            try:
                # Szukamy elementu zawierającego tekst etykiety
                label_elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{param}')]")
                
                if not label_elems:
                    print(f"   ❌ Nie znaleziono tekstu '{param}' na stronie.")
                    continue

                # Sprawdzamy każdego kandydata (czasami 'Generacja' występuje w reklamach, więc szukamy właściwego)
                for i, label in enumerate(label_elems):
                    try:
                        # Pobieramy tekst Rodzica (najczęstsza metoda w Otomoto)
                        parent = label.find_element(By.XPATH, "./..")
                        parent_text = parent.text.replace("\n", " -> ")
                        
                        # Jeśli tekst rodzica jest sensowny (nie za długi), to to jest to
                        if len(parent_text) < 100:
                            print(f"   ✅ ZNALAZŁEM! (Struktura: Rodzic)")
                            print(f"   👉 WYNIK: {parent_text}")
                            found_any = True
                            break # Przerywamy pętlę kandydatów, mamy to
                    except:
                        continue
                        
            except Exception as e:
                print(f"   ⚠️ Błąd przy szukaniu {param}: {e}")

        if found_any:
            print("\n------------------------------------------------")
            print("🎉 SUKCES! Program 'widzi' parametry.")
            print("Możemy aktualizować głównego scrapera.")
        else:
            print("\n------------------------------------------------")
            print("❌ PORAŻKA. Żadna metoda nie zadziałała.")
            print("Otomoto mogło zmienić nazwy klas lub strukturę.")

    except Exception as e:
        print(f"Błąd krytyczny: {e}")
    finally:
        print("\nZamykam za 10 sekund...")
        time.sleep(10)
        driver.quit()

if __name__ == "__main__":
    main()