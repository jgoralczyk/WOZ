from sqlite3 import connect
import aio_pika
from fastapi import FastAPI, Depends, Request, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from contextlib import asynccontextmanager
from models import Wniosek
from publisher import send_to_worker
from database import init_db, get_session

@asynccontextmanager
async def lifespan(_app: FastAPI):
    #Startup
    print("connection to MQ")
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    app.state.rabbit_con = connection
    await init_db()

    #Shutdown
    print("App is closing")

    try:
        yield
    finally:
        print("Closing MQ connection")
        await connection.close()
app = FastAPI(lifespan=lifespan)

@app.post("/wnioski/")
async def create_wniosek(
        wniosek: Wniosek,
        request: Request,
        session: AsyncSession = Depends(get_session)
):
    try:
        #zapis do bazy
        session.add(wniosek)
        await session.commit()
        await session.refresh(wniosek)

        rabbit_con = request.app.state.rabbit_con

        await send_to_worker(rabbit_con, {
            "id": wniosek.id,
            "action": "generuj_pdf",
            "title": wniosek.title #dla logów workera
        })

        return {
            "status": "Wniosek zapisany i wysłany do procesowania",
            "id": wniosek.id,
            "created_at": wniosek.created_date
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")
