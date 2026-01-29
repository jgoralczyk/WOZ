"""
Główna aplikacja FastAPI dla systemu WOZ.
REST API do zarządzania wnioskami o rozliczenie.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

import aio_pika
from fastapi import FastAPI, Depends, Request, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from database import init_db, get_session
from models import Wniosek
from publisher import send_to_worker
from auth import router as auth_router, get_current_user, require_role, User


# ============== LIFESPAN ==============

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup i shutdown aplikacji."""
    # Startup
    print("🚀 Uruchamianie aplikacji WOZ...")
    print("📡 Łączenie z RabbitMQ...")
    
    try:
        connection = await aio_pika.connect_robust(
            os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        )
        _app.state.rabbit_con = connection
        print("✅ Połączono z RabbitMQ")
    except Exception as e:
        print(f"⚠️ Nie można połączyć z RabbitMQ: {e}")
        _app.state.rabbit_con = None
    
    print("🗄️ Inicjalizacja bazy danych...")
    await init_db()
    print("✅ Baza danych gotowa")
    
    print("=" * 50)
    print("🎉 Aplikacja WOZ uruchomiona!")
    print("📖 Dokumentacja API: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        yield
    finally:
        # Shutdown
        print("\n🛑 Zamykanie aplikacji...")
        if hasattr(_app.state, 'rabbit_con') and _app.state.rabbit_con:
            await _app.state.rabbit_con.close()
            print("✅ Zamknięto połączenie z RabbitMQ")


# ============== APP ==============

app = FastAPI(
    title="WOZ API",
    description="System zarządzania wnioskami o rozliczenie",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # React dev
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)


# ============== HEALTHCHECKS ==============

@app.get("/health", tags=["Health"])
async def health_check():
    """Sprawdź status API."""
    return {"status": "healthy", "service": "WOZ API"}


@app.get("/health/db", tags=["Health"])
async def health_db(session: AsyncSession = Depends(get_session)):
    """Sprawdź połączenie z bazą danych."""
    try:
        result = await session.exec(select(Wniosek).limit(1))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )


@app.get("/health/rabbitmq", tags=["Health"])
async def health_rabbitmq(request: Request):
    """Sprawdź połączenie z RabbitMQ."""
    if hasattr(request.app.state, 'rabbit_con') and request.app.state.rabbit_con:
        if not request.app.state.rabbit_con.is_closed:
            return {"status": "healthy", "rabbitmq": "connected"}
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "rabbitmq": "disconnected"}
    )


# ============== WNIOSKI ENDPOINTS ==============

@app.post("/wnioski/", tags=["Wnioski"])
async def create_wniosek(
    wniosek: Wniosek,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Utwórz nowy wniosek.
    Wniosek zostanie zapisany w bazie i wysłany do workera do przetworzenia.
    """
    try:
        # Zapisz do bazy
        session.add(wniosek)
        await session.commit()
        await session.refresh(wniosek)
        
        # Wyślij do RabbitMQ (jeśli połączony)
        if hasattr(request.app.state, 'rabbit_con') and request.app.state.rabbit_con:
            await send_to_worker(request.app.state.rabbit_con, {
                "id": wniosek.id,
                "action": "generate_pdf",
                "title": wniosek.title
            })
            message = "Wniosek zapisany i wysłany do procesowania"
        else:
            message = "Wniosek zapisany (RabbitMQ niedostępny - PDF nie będzie wygenerowany)"
        
        return {
            "status": message,
            "id": wniosek.id,
            "created_at": wniosek.created_date
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")


@app.get("/wnioski/", tags=["Wnioski"])
async def get_wnioski(
    user: str = Query(..., description="Nazwa użytkownika"),
    role: str = Query("user", description="Rola: 'user' (tylko własne) lub 'payroll' (wszystkie)"),
    status_filter: Optional[str] = Query(None, description="Filtruj po statusie"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session)
):
    """
    Pobierz listę wniosków.
    - Rola 'user': tylko wnioski danego użytkownika
    - Rola 'payroll': wszystkie wnioski
    """
    statement = select(Wniosek)
    
    # Filtruj po właścicielu dla zwykłych użytkowników
    if role != "payroll":
        statement = statement.where(Wniosek.owner == user)
    
    # Filtruj po statusie (opcjonalne)
    if status_filter:
        statement = statement.where(Wniosek.status == status_filter)
    
    # Paginacja
    statement = statement.offset(offset).limit(limit)
    
    # Sortuj po dacie (najnowsze najpierw)
    statement = statement.order_by(Wniosek.created_date.desc())
    
    result = await session.execute(statement)
    wnioski = result.scalars().all()
    
    return wnioski


@app.get("/wnioski/{wniosek_id}", tags=["Wnioski"])
async def get_wniosek(
    wniosek_id: int = Path(..., description="ID wniosku"),
    session: AsyncSession = Depends(get_session)
):
    """Pobierz szczegóły pojedynczego wniosku."""
    result = await session.execute(select(Wniosek).where(Wniosek.id == wniosek_id))
    wniosek = result.scalars().first()
    
    if not wniosek:
        raise HTTPException(status_code=404, detail="Wniosek nie znaleziony")
    
    return wniosek


@app.put("/wnioski/{wniosek_id}/status", tags=["Wnioski"])
async def update_wniosek_status(
    wniosek_id: int = Path(..., description="ID wniosku"),
    new_status: str = Query(..., description="Nowy status"),
    session: AsyncSession = Depends(get_session)
):
    """
    Zmień status wniosku.
    Dozwolone statusy: Waiting, Processing, Completed, Failed, Rejected
    """
    allowed_statuses = ["Waiting", "Processing", "Completed", "Failed", "Rejected"]
    
    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Nieprawidłowy status. Dozwolone: {', '.join(allowed_statuses)}"
        )
    
    result = await session.execute(select(Wniosek).where(Wniosek.id == wniosek_id))
    wniosek = result.scalars().first()
    
    if not wniosek:
        raise HTTPException(status_code=404, detail="Wniosek nie znaleziony")
    
    old_status = wniosek.status
    wniosek.status = new_status
    session.add(wniosek)
    await session.commit()
    
    return {
        "message": "Status zaktualizowany",
        "wniosek_id": wniosek_id,
        "old_status": old_status,
        "new_status": new_status
    }


@app.delete("/wnioski/{wniosek_id}", tags=["Wnioski"])
async def delete_wniosek(
    wniosek_id: int = Path(..., description="ID wniosku"),
    session: AsyncSession = Depends(get_session)
):
    """Usuń wniosek."""
    result = await session.execute(select(Wniosek).where(Wniosek.id == wniosek_id))
    wniosek = result.scalars().first()
    
    if not wniosek:
        raise HTTPException(status_code=404, detail="Wniosek nie znaleziony")
    
    await session.delete(wniosek)
    await session.commit()
    
    return {"message": "Wniosek usunięty", "wniosek_id": wniosek_id}


@app.get("/wnioski/{wniosek_id}/pdf", tags=["Wnioski"])
async def download_pdf(
    wniosek_id: int = Path(..., description="ID wniosku")
):
    """Pobierz wygenerowany PDF dla wniosku."""
    pdf_dir = os.getenv("PDF_OUTPUT_DIR", "./generated_pdfs")
    
    # Szukaj pliku PDF dla danego wniosku
    if os.path.exists(pdf_dir):
        for filename in os.listdir(pdf_dir):
            if filename.startswith(f"wniosek_{wniosek_id}_") and filename.endswith(".pdf"):
                filepath = os.path.join(pdf_dir, filename)
                return FileResponse(
                    filepath,
                    media_type="application/pdf",
                    filename=filename
                )
    
    raise HTTPException(status_code=404, detail="PDF nie znaleziony. Upewnij się, że wniosek został przetworzony.")


# ============== STATYSTYKI ==============

@app.get("/stats/", tags=["Statystyki"])
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Pobierz statystyki wniosków."""
    # Wszystkie wnioski
    result = await session.execute(select(Wniosek))
    all_wnioski = result.scalars().all()
    
    # Statystyki
    total = len(all_wnioski)
    by_status = {}
    total_payoff = 0.0
    
    for w in all_wnioski:
        status = w.status or "Unknown"
        by_status[status] = by_status.get(status, 0) + 1
        total_payoff += w.payoff or 0
    
    return {
        "total_wnioski": total,
        "by_status": by_status,
        "total_payoff": round(total_payoff, 2),
        "avg_payoff": round(total_payoff / total, 2) if total > 0 else 0
    }
