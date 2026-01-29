"""
Worker RabbitMQ do asynchronicznego przetwarzania wniosków.
Generuje PDF i aktualizuje status wniosku w bazie danych.
"""

import asyncio
import json
import os
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import select

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Import modelu
from models import Wniosek

# Konfiguracja
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./wnioski.db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "./generated_pdfs")

# Upewnij się, że folder na PDF istnieje
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# Setup database
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def update_wniosek_status(wniosek_id: int, status: str, pdf_path: str = None):
    """Aktualizuje status wniosku w bazie danych."""
    async with SessionLocal() as session:
        result = await session.execute(select(Wniosek).where(Wniosek.id == wniosek_id))
        wniosek = result.scalars().first()
        if wniosek:
            wniosek.status = status
            session.add(wniosek)
            await session.commit()
            print(f"[✓] Status wniosku {wniosek_id} zmieniony na: {status}")
            return True
        return False


async def get_wniosek(wniosek_id: int) -> Wniosek:
    """Pobiera wniosek z bazy danych."""
    async with SessionLocal() as session:
        result = await session.execute(select(Wniosek).where(Wniosek.id == wniosek_id))
        return result.scalars().first()


def generate_pdf(wniosek: Wniosek) -> str:
    """Generuje PDF z danymi wniosku. Zwraca ścieżkę do pliku."""
    
    filename = f"wniosek_{wniosek.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(PDF_OUTPUT_DIR, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2563eb')
    )
    
    normal_style = styles['Normal']
    
    # Build document
    elements = []
    
    # Header
    elements.append(Paragraph("WNIOSEK O ROZLICZENIE", title_style))
    elements.append(Paragraph(f"Nr: WOZ/{wniosek.id}/{datetime.now().year}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Dane podstawowe
    elements.append(Paragraph("Dane podstawowe", heading_style))
    
    data = [
        ["Tytuł:", wniosek.title or "-"],
        ["Osoba odpowiedzialna:", wniosek.person or "-"],
        ["Firma / Kontrahent:", wniosek.company or "-"],
        ["Typ pojazdu:", wniosek.type_of_woz or "-"],
        ["Kwota rozliczenia:", f"{wniosek.payoff:,.2f} PLN" if wniosek.payoff else "-"],
        ["Miesiąc rozliczeniowy:", wniosek.billing_month or "-"],
        ["Data utworzenia:", wniosek.created_date.strftime('%Y-%m-%d %H:%M') if wniosek.created_date else "-"],
    ]
    
    table = Table(data, colWidths=[5*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Okres premii
    if wniosek.premia_start or wniosek.premia_end:
        elements.append(Paragraph("Okres premii", heading_style))
        premia_data = [
            ["Data początkowa:", wniosek.premia_start or "-"],
            ["Data końcowa:", wniosek.premia_end or "-"],
        ]
        premia_table = Table(premia_data, colWidths=[5*cm, 10*cm])
        premia_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(premia_table)
        elements.append(Spacer(1, 20))
    
    # Godziny pracy
    if wniosek.hours and isinstance(wniosek.hours, dict) and len(wniosek.hours) > 0:
        elements.append(Paragraph("Godziny pracy", heading_style))
        hours_data = [[k, str(v)] for k, v in wniosek.hours.items()]
        hours_table = Table(hours_data, colWidths=[5*cm, 10*cm])
        hours_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(hours_table)
        elements.append(Spacer(1, 20))
    
    # Komentarz
    if wniosek.comment:
        elements.append(Paragraph("Komentarz", heading_style))
        elements.append(Paragraph(wniosek.comment, normal_style))
        elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Wygenerowano automatycznie: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    ))
    elements.append(Paragraph(
        f"Status: {wniosek.status}",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    
    return filepath


async def process_message(message: IncomingMessage):
    """Przetwarza wiadomość z kolejki RabbitMQ."""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            wniosek_id = data.get("id")
            action = data.get("action")
            
            print(f"\n[→] Otrzymano zadanie: {action} dla wniosku ID={wniosek_id}")
            
            if action == "generate_pdf":
                # Zmień status na Processing
                await update_wniosek_status(wniosek_id, "Processing")
                
                # Pobierz dane wniosku
                wniosek = await get_wniosek(wniosek_id)
                if not wniosek:
                    print(f"[✗] Wniosek {wniosek_id} nie znaleziony!")
                    return
                
                # Generuj PDF
                print(f"[...] Generowanie PDF dla wniosku: {wniosek.title}")
                pdf_path = generate_pdf(wniosek)
                print(f"[✓] PDF wygenerowany: {pdf_path}")
                
                # Zmień status na Completed
                await update_wniosek_status(wniosek_id, "Completed")
                
            else:
                print(f"[?] Nieznana akcja: {action}")
                
        except Exception as e:
            print(f"[✗] Błąd przetwarzania: {e}")
            if 'wniosek_id' in locals():
                await update_wniosek_status(wniosek_id, "Failed")


async def main():
    """Główna funkcja workera."""
    print("=" * 50)
    print("🚀 WOZ Worker - uruchamianie...")
    print(f"📁 PDF Output: {PDF_OUTPUT_DIR}")
    print(f"🐰 RabbitMQ: {RABBITMQ_URL}")
    print("=" * 50)
    
    # Połącz z RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        
        # Ustaw prefetch (ile wiadomości na raz)
        await channel.set_qos(prefetch_count=1)
        
        # Deklaruj kolejkę
        queue = await channel.declare_queue("wnioski_queue", durable=True)
        
        print(f"\n[*] Oczekiwanie na wiadomości w kolejce 'wnioski_queue'...")
        print("[*] Naciśnij CTRL+C aby zakończyć\n")
        
        # Konsumuj wiadomości
        await queue.consume(process_message)
        
        # Czekaj w nieskończoność
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Worker zatrzymany przez użytkownika")
