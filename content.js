// content.js - Analizator Otomoto

console.log("🚀 Otomoto AI Analyzer: Startuję...");

// 1. SYMULACJA TWOJEGO MODELU (MÓZGU)
// Docelowo tutaj będzie zapytanie do Twojego Pythona.
// Na razie robimy prostą matematykę, żebyś widział efekt.
function evaluateCar(carParams, price) {
    let year = 2015;
    let horsePower = 100;
    
    // Wyciągamy rok i moc z parametrów
    carParams.forEach(param => {
        if (param.key === 'year') year = parseInt(param.value);
        if (param.key === 'engine_power') horsePower = parseInt(param.value);
    });

    // PROSTY ALGORYTM TESTOWY:
    // Zakładamy, że 1 koń mechaniczny jest wart 200 zł, a każdy rok auta 5000 zł :)
    // To tylko przykład, żeby pokazać różne kolory!
    const theoreticalValue = (horsePower * 250) + ((year - 2000) * 3000); 
    
    const ratio = price / theoreticalValue;

    if (ratio < 0.8) return { color: "#00ff00", label: "SUPER OKAZJA", score: "A+" }; // Zielony
    if (ratio < 1.2) return { color: "#ffcc00", label: "CENA OK", score: "B" };       // Żółty
    return { color: "#ff0000", label: "DROGO", score: "C" };                          // Czerwony
}

// 2. GŁÓWNA FUNKCJA POBIERAJĄCA DANE
function runAnalysis() {
    try {
        const rawData = document.getElementById('__NEXT_DATA__').innerText;
        const jsonData = JSON.parse(rawData);
        const urqlCache = jsonData.props.pageProps.urqlState;

        // Szukamy listy aut w cache (Twoim sprawdzonym sposobem)
        Object.keys(urqlCache).forEach(key => {
            try {
                const data = JSON.parse(urqlCache[key].data);
                // Sprawdzamy czy to lista wyników
                let listLocation = null;
                if (data.advertSearch && data.advertSearch.edges) listLocation = data.advertSearch.edges;
                else if (data.search && data.search.results) listLocation = data.search.results;

                if (listLocation && Array.isArray(listLocation) && listLocation.length > 0) {
                    console.log(`✅ Znalazłem paczkę ${listLocation.length} aut! Analizuję...`);
                    processCars(listLocation);
                }
            } catch (err) {}
        });

    } catch (e) {
        console.log("Jeszcze nie załadowano danych, czekam...");
    }
}

// 3. MALOWANIE PO EKRANIE
function processCars(carsList) {
    carsList.forEach(item => {
        const car = item.node || item; // Czasami dane są w 'node'
        
        // Wyciągamy kluczowe dane
        const url = car.url;
        const price = car.price ? parseFloat(car.price.amount || car.price.value) : 0;
        const params = car.parameters || [];

        // Oceniamy auto (Symulacja AI)
        const rating = evaluateCar(params, price);

        // Znajdujemy auto na ekranie po linku
        // Szukamy elementu <a> który ma taki sam href jak w danych
        const linkElement = document.querySelector(`a[href="${url}"]`);
        
        if (linkElement) {
            // Znajdujemy główny kontener (rodzica), żeby tam wkleić pasek
            // W Otomoto zazwyczaj trzeba wyjść kilka pięter w górę od linku
            const articleBox = linkElement.closest('article');

            if (articleBox && !articleBox.querySelector('.ai-badge')) {
                // Tworzymy nasz pasek oceny
                const badge = document.createElement('div');
                badge.className = 'ai-badge';
                badge.style.position = 'absolute';
                badge.style.top = '10px';
                badge.style.left = '10px';
                badge.style.zIndex = '9999';
                badge.style.padding = '5px 10px';
                badge.style.fontWeight = 'bold';
                badge.style.color = 'black';
                badge.style.backgroundColor = rating.color;
                badge.style.borderRadius = '5px';
                badge.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';
                badge.innerHTML = `AI: ${rating.label} (${rating.score})`;

                // Wklejamy go do oferty
                articleBox.style.position = 'relative'; // Żeby badge się dobrze ustawił
                articleBox.appendChild(badge);
            }
        }
    });
}

// Uruchomienie (z lekkim opóźnieniem, żeby strona zdążyła się zbudować)
setTimeout(runAnalysis, 2000);

// Ponowne uruchomienie przy przewijaniu (Otomoto może doczytywać auta)
window.addEventListener('scroll', () => {
    // Prosty debouncing, żeby nie odpalać za często
    if(Math.random() > 0.8) runAnalysis();
});