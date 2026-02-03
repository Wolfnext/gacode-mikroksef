# GACODE mikroKSeF

Open source i cloud-ready klient webowy do obsługi **Krajowego Systemu e-Faktur (KSeF)** w Polsce, rozwijany przez GACODE.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)

## Spis treści

- [Funkcjonalności](#funkcjonalności)
- [Architektura](#architektura)
- [Wymagania](#wymagania)
- [Instalacja](#instalacja)
- [Konfiguracja](#konfiguracja)
- [Uruchomienie](#uruchomienie)
- [Użytkowanie](#użytkowanie)
- [API](#api)
- [Testowanie](#testowanie)
- [Środowiska KSeF](#środowiska-ksef)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Licencja](#licencja)

## Funkcjonalności

### Zaimplementowane

- **Uwierzytelnianie z KSeF** - Metoda tokenowa z szyfrowaniem RSA/AES
- **Przeglądanie faktur** - Lista faktur wystawionych i otrzymanych
- **Filtrowanie** - Po dacie, typie, NIP kontrahenta
- **Szczegóły faktury** - Podgląd nagłówka i treści XML
- **Pobieranie** - Eksport faktur w formacie XML
- **Synchronizacja** - Automatyczne pobieranie faktur z KSeF
- **Cache lokalny** - SQLite do przechowywania faktur offline
- **Zarządzanie sesją** - Automatyczne odświeżanie i kończenie sesji

### Planowane

- Wysyłanie nowych faktur
- Pobieranie UPO (Urzędowe Poświadczenie Odbioru)
- Uwierzytelnianie podpisem kwalifikowanym (XAdES)
- Raportowanie faktur fałszywych
- Eksport do PDF

## Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│                    http://localhost:3000                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│                    http://localhost:8000                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ KSeF Client │  │ Crypto Svc  │  │ Session Manager     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                         │                                   │
│                         ▼                                   │
│                  ┌─────────────┐                           │
│                  │  SQLite DB  │                           │
│                  └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      KSeF API                               │
│              ksef-test.mf.gov.pl/api                        │
└─────────────────────────────────────────────────────────────┘
```

## Wymagania

### Backend
- Python 3.11 lub nowszy
- pip

### Frontend
- Node.js 18 lub nowszy
- npm

### Opcjonalnie
- Docker i Docker Compose

## Instalacja

### Metoda 1: Instalacja lokalna

```bash
# Klonowanie repozytorium
git clone https://github.com/Wolfnext/gacode-mikroksef.git
cd mikroksef

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Metoda 2: Docker

```bash
git clone https://github.com/Wolfnext/gacode-mikroksef.git
cd mikroksef
docker-compose build
```

### Metoda 3: Make

```bash
git clone https://github.com/Wolfnext/gacode-mikroksef.git
cd mikroksef
make install
```

## Konfiguracja

### 1. Utwórz plik konfiguracyjny

```bash
cp .env.example .env
```

### 2. Edytuj plik `.env`

```env
# Środowisko KSeF: test, demo, production
KSEF_ENVIRONMENT=test

# NIP firmy (10 cyfr)
COMPANY_NIP=1234567890

# Token autoryzacyjny KSeF
KSEF_AUTH_TOKEN=twoj-token-ksef

# Klucz szyfrowania (wygeneruj: openssl rand -hex 32)
SECRET_KEY=wygenerowany-klucz-32-bajty
```

### 3. Uzyskanie tokena KSeF

1. Wejdź na portal KSeF: https://ksef-test.mf.gov.pl
2. Zaloguj się podpisem kwalifikowanym lub Profilem Zaufanym
3. Przejdź do: **Poświadczenia** → **Generuj token**
4. Skopiuj wygenerowany token do pliku `.env`

### Opis zmiennych środowiskowych

| Zmienna | Opis | Wartość domyślna |
|---------|------|------------------|
| `KSEF_ENVIRONMENT` | Środowisko KSeF | `test` |
| `KSEF_API_URL` | Nadpisanie URL API | (auto) |
| `COMPANY_NIP` | NIP firmy | - |
| `KSEF_AUTH_TOKEN` | Token autoryzacyjny | - |
| `DATABASE_URL` | Ścieżka do bazy SQLite | `sqlite:///./mikroksef.db` |
| `SECRET_KEY` | Klucz szyfrowania JWT | - |
| `DEBUG` | Tryb debugowania | `true` |
| `LOG_LEVEL` | Poziom logowania | `INFO` |

## Uruchomienie

### Metoda 1: Lokalna (deweloperska)

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Metoda 2: Make

```bash
make dev
```

### Metoda 3: Docker

```bash
# Produkcja
docker-compose up -d

# Deweloperska (z hot reload)
docker-compose -f docker-compose.dev.yml up
```

### Dostęp do aplikacji

| Serwis | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Dokumentacja API (Swagger) | http://localhost:8000/docs |
| Dokumentacja API (ReDoc) | http://localhost:8000/redoc |

## Użytkowanie

### 1. Logowanie

1. Otwórz http://localhost:3000
2. Wprowadź NIP firmy (10 cyfr)
3. Kliknij **Zaloguj**

### 2. Dashboard

- **Faktury wystawione** - faktury, gdzie jesteś sprzedawcą
- **Faktury otrzymane** - faktury, gdzie jesteś nabywcą
- Kliknij **Synchronizuj** aby pobrać faktury z KSeF

### 3. Lista faktur

- Przełączaj między **Wystawione** / **Otrzymane**
- Użyj filtrów (data, typ, NIP)
- Kliknij na fakturę aby zobaczyć szczegóły
- Pobierz fakturę jako XML

### 4. Wylogowanie

- Kliknij **Wyloguj** w nagłówku
- Sesja KSeF zostanie automatycznie zakończona

## API

### Endpointy

#### Uwierzytelnianie

| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/api/auth/session/init-token` | Inicjalizacja sesji |
| GET | `/api/auth/session/status` | Status sesji |
| POST | `/api/auth/session/terminate` | Zakończenie sesji |

#### Faktury

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/invoices` | Lista faktur |
| GET | `/api/invoices/{ref}` | Szczegóły faktury |
| GET | `/api/invoices/{ref}/download` | Pobierz XML |
| GET | `/api/invoices/{ref}/status` | Status faktury |

#### Synchronizacja

| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/api/sync` | Synchronizuj faktury |
| POST | `/api/sync/issued` | Synchronizuj wystawione |
| POST | `/api/sync/received` | Synchronizuj otrzymane |
| GET | `/api/sync/status` | Status synchronizacji |
| DELETE | `/api/sync/cache` | Wyczyść cache |

### Przykłady cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Inicjalizacja sesji
curl -X POST http://localhost:8000/api/auth/session/init-token \
  -H "Content-Type: application/json" \
  -d '{"nip": "1234567890"}'

# Lista faktur wystawionych
curl "http://localhost:8000/api/invoices?subjectType=subject1"

# Lista faktur otrzymanych
curl "http://localhost:8000/api/invoices?subjectType=subject2"

# Szczegóły faktury
curl "http://localhost:8000/api/invoices/1234567890-20260203-ABC123-XY"

# Pobierz XML
curl -O "http://localhost:8000/api/invoices/1234567890-20260203-ABC123-XY/download"

# Synchronizuj faktury
curl -X POST "http://localhost:8000/api/sync/issued"

# Zakończ sesję
curl -X POST http://localhost:8000/api/auth/session/terminate
```

## Testowanie

### Backend (pytest)

```bash
cd backend
source venv/bin/activate

# Wszystkie testy
pytest tests/ -v

# Z pokryciem kodu
pytest tests/ -v --cov=app --cov-report=html

# Konkretny plik
pytest tests/test_auth.py -v
```

### Frontend (Cypress)

```bash
cd frontend

# Uruchom testy
npm run test

# Tryb interaktywny
npm run test:open
```

### Make

```bash
# Wszystkie testy
make test

# Tylko backend
make test-backend

# Tylko frontend
make test-frontend
```

## Środowiska KSeF

| Środowisko | URL | Opis |
|------------|-----|------|
| **Test** | `https://ksef-test.mf.gov.pl/api` | Środowisko testowe z fikcyjnymi danymi |
| **Demo** | `https://ksef-demo.mf.gov.pl/api` | Środowisko demonstracyjne |
| **Produkcja** | `https://ksef.mf.gov.pl/api` | Środowisko produkcyjne (od 01.02.2026) |

### Przełączanie środowiska

Edytuj `.env`:

```env
# Test
KSEF_ENVIRONMENT=test

# Demo
KSEF_ENVIRONMENT=demo

# Produkcja (UWAGA: prawdziwe faktury!)
KSEF_ENVIRONMENT=production
```

## Rozwiązywanie problemów

### "No active KSeF session"

**Przyczyna:** Sesja wygasła lub nie została zainicjowana.

**Rozwiązanie:**
1. Sprawdź czy token autoryzacyjny jest aktualny
2. Upewnij się że NIP jest poprawny
3. Zainicjuj nową sesję

### "Rate limit exceeded"

**Przyczyna:** Przekroczono limity API KSeF (100 req/s, 300 req/min, 1200 req/h).

**Rozwiązanie:**
1. Poczekaj i spróbuj ponownie
2. Sprawdź nagłówek `Retry-After` w odpowiedzi

### "Authentication failed"

**Przyczyna:** Nieprawidłowy token lub problem z szyfrowaniem.

**Rozwiązanie:**
1. Wygeneruj nowy token w portalu KSeF
2. Sprawdź czy `COMPANY_NIP` zgadza się z NIP w tokenie

### Problemy z połączeniem

**Rozwiązanie:**
1. Sprawdź firewall i ustawienia proxy
2. Upewnij się że masz dostęp do `ksef-test.mf.gov.pl`
3. Sprawdź logi: `docker-compose logs backend`

### Błędy bazy danych

**Rozwiązanie:**
```bash
# Zresetuj bazę danych
make db-reset

# Lub ręcznie
rm backend/data/*.db
```

## Struktura projektu

```
mikroKSeF/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── api/               # Endpointy REST
│   │   ├── models/            # Modele Pydantic
│   │   ├── services/          # Logika biznesowa
│   │   └── utils/             # Pomocnicze funkcje
│   └── tests/                 # Testy pytest
├── frontend/                   # Next.js React
│   ├── src/
│   │   ├── app/              # Strony (App Router)
│   │   ├── components/       # Komponenty UI
│   │   ├── hooks/            # React hooks
│   │   ├── lib/              # API client
│   │   └── types/            # TypeScript types
│   └── cypress/              # Testy E2E
├── docker-compose.yml         # Konfiguracja Docker
├── Makefile                   # Komendy make
└── README.md                  # Dokumentacja
```

## Zasoby

- [Oficjalny portal KSeF](https://ksef.podatki.gov.pl)
- [Dokumentacja API KSeF](https://github.com/CIRFMF/ksef-docs)
- [FAQ KSeF](https://ksef.podatki.gov.pl/faq)
- [Schemat FA_VAT](https://www.gov.pl/web/kas/struktury-logiczne-e-faktur)

## Wsparcie

- **Telefon KSeF:** 22 330 03 30
- **E-mail:** info.ksef@mf.gov.pl
- **Godziny:** pon-pt 7:00-19:00

## Licencja

MIT License - zobacz [LICENSE](LICENSE). Projekt jest open source. Oprogramowanie dostarczane jest "AS IS", bez gwarancji; autorzy nie ponoszą odpowiedzialności za szkody.

---

**Uwaga:** Obowiązkowe korzystanie z KSeF wchodzi w życie **1 lutego 2026** dla większości przedsiębiorców.
