"""Support Tickets API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import SupportTicketCreate, SupportTicketResponse
from app.core.security import get_current_user
from app.services import get_support_service

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=SupportTicketResponse)
async def create_ticket(data: SupportTicketCreate, current_user: dict = Depends(get_current_user)):
    ticket = get_support_service().create_ticket(current_user["user_id"], data.model_dump())
    return ticket


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def get_tickets(current_user: dict = Depends(get_current_user)):
    return get_support_service().get_user_tickets(current_user["user_id"])


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    tickets = get_support_service().get_user_tickets(current_user["user_id"])
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    raise HTTPException(status_code=404, detail="Ticket not found")
