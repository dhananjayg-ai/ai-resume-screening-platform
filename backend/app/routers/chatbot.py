"""HR chatbot endpoint: rule-based intent matching over the DB."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.chatbot.engine import answer_query
from app.database import get_db
from app.schemas import ChatbotQueryRequest, ChatbotQueryResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_model=ChatbotQueryResponse)
def chatbot_query(payload: ChatbotQueryRequest, db: Session = Depends(get_db)):
    response_text = answer_query(db, payload.query)

    log_entry = models.ChatbotQueryLog(query_text=payload.query, response_text=response_text)
    db.add(log_entry)
    db.commit()

    return ChatbotQueryResponse(query=payload.query, response=response_text)
