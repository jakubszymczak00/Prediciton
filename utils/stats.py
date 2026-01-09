class SessionStats:
    def __init__(self):
        self.processed = 0
        self.new = 0
        self.updated_price = 0
        self.seen = 0
        self.errors = 0
        
    def add_processed(self):
        self.processed += 1
        
    def add_new(self):
        self.new += 1
        
    def add_price_change(self):
        self.updated_price += 1
        
    def add_seen(self):
        self.seen += 1
        
    def add_error(self):
        self.errors += 1
        
    def get_summary(self):
        return (
            f"--- RAPORT SESJI ---\n"
            f"Przetworzono ofert: {self.processed}\n"
            f"Nowe oferty: {self.new}\n"
            f"Zmiany cen: {self.updated_price}\n"
            f"Bez zmian: {self.seen}\n"
            f"Bledy: {self.errors}\n"
            f"--------------------"
        )