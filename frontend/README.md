# OpenAvatarChat Frontend

Nowoczesny interfejs webowy dla polskiego asystenta AI z funkcją avatara.

## 🚀 Funkcje

- **💬 Chat tekstowy** - Pisz wiadomości do asystenta AI
- **🎤 Rozpoznawanie mowy** - Mów do asystenta (naciśnij i trzymaj przycisk mikrofonu)
- **🔊 Synteza mowy** - Asystent odpowiada głosem (polski głos Gosia)
- **👤 Avatar wideo** - Wizualna reprezentacja asystenta z animacjami lip-sync
- **⚡ Automatyczna inicjalizacja** - Wszystkie funkcje uruchamiają się automatycznie
- **📱 Responsywny design** - Działa na komputerach, tabletach i telefonach
- **⚙️ Ustawienia** - Konfiguracja URL API, mikrofonu, avatara

## 🛠️ Instalacja i uruchomienie

### Wymagania
- Python 3.7+
- Uruchomiony serwer API OpenAvatarChat (port 8000)

### Szybkie uruchomienie

1. **Uruchom serwer API** (w osobnym terminalu):
```bash
cd /home/arti/Repos/OpenAvatarChat/api
python main.py
```

2. **Uruchom frontend**:
```bash
cd /home/arti/Repos/OpenAvatarChat/frontend
python serve.py
```

3. **Otwórz w przeglądarce**:
```
http://localhost:3000
```

### Alternatywne porty

Jeśli port 3000 jest zajęty:
```bash
python serve.py --port 3001
```

## 🎯 Jak używać

### Chat tekstowy
1. Wpisz wiadomość w polu tekstowym
2. Naciśnij Enter lub kliknij przycisk wyślij
3. Asystent odpowie głosem i tekstem

### Chat głosowy
1. Naciśnij i trzymaj przycisk mikrofonu 🎤
2. Mów do mikrofonu
3. Puść przycisk aby zakończyć nagrywanie
4. Asystent przetworzy mowę i odpowie

### Skróty klawiszowe
- **Enter** - Wyślij wiadomość tekstową
- **Spacja** - Naciśnij i trzymaj do nagrywania głosu
- **Escape** - Zamknij ustawienia

## ⚙️ Ustawienia

Kliknij ikonę koła zębatego aby skonfigurować:

- **URL API** - Adres serwera backend (domyślnie http://localhost:8000)
- **Rozpoznawanie mowy** - Włącz/wyłącz funkcje głosowe
- **Automatyczne odtwarzanie** - Automatyczne odtwarzanie odpowiedzi AI
- **Wyświetlanie avatara** - Włącz/wyłącz animacje avatara

## 🔧 Struktura plików

```
frontend/
├── index.html          # Główna strona
├── styles.css          # Style CSS
├── serve.py           # Serwer HTTP
├── js/
│   ├── config.js      # Zarządzanie konfiguracją
│   ├── api.js         # Komunikacja z API
│   ├── audio.js       # Nagrywanie i odtwarzanie audio
│   ├── avatar.js      # Zarządzanie avatarem
│   ├── chat.js        # Interfejs chatu
│   └── app.js         # Główna aplikacja
└── README.md          # Ten plik
```

## 🌐 Kompatybilność przeglądarek

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

### Wymagane uprawnienia przeglądarki
- **Mikrofon** - Dla funkcji rozpoznawania mowy
- **Autoplay** - Dla automatycznego odtwarzania odpowiedzi

## 🐛 Rozwiązywanie problemów

### Mikrofon nie działa
1. Sprawdź uprawnienia mikrofonu w przeglądarce
2. Upewnij się, że używasz HTTPS lub localhost
3. Sprawdź czy mikrofon nie jest używany przez inną aplikację

### API nie odpowiada
1. Sprawdź czy serwer API jest uruchomiony (port 8000)
2. Sprawdź URL API w ustawieniach
3. Sprawdź konsole przeglądarki (F12)

### Avatar nie wyświetla się
1. Sprawdź czy avatar jest włączony w ustawieniach
2. Sprawdź czy serwer API ma dostęp do modeli avatara
3. Sprawdź połączenie sieciowe

### Brak dźwięku
1. Sprawdź głośność systemu
2. Sprawdź czy autoplay jest włączony w ustawieniach
3. Kliknij w okno przeglądarki aby aktywować autoplay

## 🚀 Funkcje zaawansowane

### Automatyczna inicjalizacja
Frontend automatycznie:
- Nawiązuje połączenie z API
- Inicjalizuje wszystkie komponenty AI
- Sprawdza dostępność mikrofonu
- Przygotowuje avatar do pracy

### Obsługa błędów
- Automatyczne ponawianie połączeń
- Graceful degradation (wyłączanie funkcji w przypadku błędów)
- Informatywne komunikaty o błędach
- Fallback dla nieobsługiwanych funkcji

### Wydajność
- Lazy loading komponentów
- Optymalizowane animacje CSS
- Minimalne zużycie pamięci
- Szybkie ładowanie strony

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi w konsoli przeglądarki (F12)
2. Sprawdź logi serwera API
3. Sprawdź dokumentację API

---

**OpenAvatarChat Frontend v1.0.0**  
Polski asystent AI z awatarem - interfejs webowy
