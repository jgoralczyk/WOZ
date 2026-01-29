# 🚗 WOZ - System Wniosków o Rozliczenie

[![CI/CD](https://github.com/jgoralczyk/WOZ/actions/workflows/ci.yml/badge.svg)](https://github.com/jgoralczyk/WOZ/actions/workflows/ci.yml)

System do zarządzania wnioskami o rozliczenie dla firm transportowych/logistycznych.

## 🏗️ Stack technologiczny

| Warstwa | Technologia |
|---------|-------------|
| **Backend** | FastAPI, SQLModel, Pydantic |
| **Frontend** | React 19, Vite, React Router |
| **Baza danych** | PostgreSQL (prod) / SQLite (dev) |
| **Message Queue** | RabbitMQ + aio-pika |
| **Autentykacja** | JWT (python-jose + bcrypt) |
| **PDF** | ReportLab |
| **Konteneryzacja** | Docker, Docker Compose |

## 📁 Struktura projektu

```
WOZ/
├── main.py              # FastAPI aplikacja
├── auth.py              # System autentykacji JWT
├── models.py            # Modele SQLModel
├── database.py          # Konfiguracja bazy danych
├── publisher.py         # RabbitMQ publisher
├── worker.py            # Worker do generowania PDF
├── requirements.txt     # Zależności Python
├── Dockerfile           # Docker dla backendu
├── docker-compose.yml   # Orkiestracja kontenerów
│
├── frontend/            # Aplikacja React
│   ├── src/
│   │   ├── context/     # AuthContext
│   │   ├── pages/       # Strony (Login, Register, Dashboard, List, Form)
│   │   ├── components/  # Komponenty (Navbar)
│   │   └── App.jsx      # Główny komponent
│   ├── Dockerfile
│   └── nginx.conf
│
├── tests/               # Testy pytest
│   ├── conftest.py
│   ├── test_api.py
│   └── test_auth.py
│
└── .github/workflows/   # CI/CD
    └── ci.yml
```

## 🚀 Szybki start

### Wymagania
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (dla produkcji)

### Uruchomienie lokalne (development)

#### 1. Backend

```bash
# Utwórz wirtualne środowisko
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate   # Windows

# Zainstaluj zależności
pip install -r requirements.txt

# Uruchom RabbitMQ (Docker)
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Uruchom API
uvicorn main:app --reload
```

API dostępne pod: http://localhost:8000
Dokumentacja Swagger: http://localhost:8000/docs

#### 2. Worker (w osobnym terminalu)

```bash
python worker.py
```

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dostępny pod: http://localhost:5173

### Uruchomienie z Docker Compose (produkcja)

```bash
# Utwórz plik .env
cp .env.example .env
# Edytuj .env i ustaw bezpieczne wartości

# Uruchom wszystkie serwisy
docker-compose up -d

# Sprawdź logi
docker-compose logs -f
```

Serwisy:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- RabbitMQ Management: http://localhost:15672

## 📖 API Endpoints

### Autentykacja
| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/auth/register` | Rejestracja użytkownika |
| POST | `/auth/login` | Logowanie |
| POST | `/auth/refresh` | Odświeżenie tokena |
| GET | `/auth/me` | Dane zalogowanego użytkownika |

### Wnioski
| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/wnioski/` | Lista wniosków |
| POST | `/wnioski/` | Utwórz wniosek |
| GET | `/wnioski/{id}` | Szczegóły wniosku |
| PUT | `/wnioski/{id}/status` | Zmień status |
| DELETE | `/wnioski/{id}` | Usuń wniosek |
| GET | `/wnioski/{id}/pdf` | Pobierz PDF |

### Statystyki
| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/stats/` | Statystyki wniosków |

### Health checks
| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/health` | Status API |
| GET | `/health/db` | Status bazy danych |
| GET | `/health/rabbitmq` | Status RabbitMQ |

## 🧪 Testy

```bash
# Zainstaluj zależności testowe
pip install pytest pytest-asyncio pytest-cov httpx

# Uruchom testy
pytest tests/ -v

# Z coverage
pytest tests/ -v --cov=. --cov-report=html
```

## 🔐 Bezpieczeństwo

- Hasła hashowane z bcrypt
- JWT tokeny z czasem wygaśnięcia
- Refresh tokeny do odświeżania sesji
- CORS skonfigurowany dla dozwolonych origins
- Role-based access control (user, payroll, admin)

## 📄 Licencja

MIT License

## 👨‍💻 Autor

Projekt na zaliczenie przedmiotu "Programowanie Sieciowe"
