from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from infrastructure.database.connection import get_db
from infrastructure.auth.security import verificar_token_externo

router = APIRouter(
    prefix="/api/v1/ia/agendamentos",
    tags=["Integração Oracle - Agendamentos"]
)

@router.post("/", dependencies=[Depends(verificar_token_externo)])
def criar_agendamento_no_oracle(db: Session = Depends(get_db)):
    """
    Recebe os dados estruturados da IA e faz o INSERT na tabela do Oracle.
    """
    pass

@router.patch("/{id}/status", dependencies=[Depends(verificar_token_externo)])
def atualizar_status_agendamento(id: int, db: Session = Depends(get_db)):
    """
    Atualiza o estado de um evento no banco Oracle (CONFIRMAR, CANCELAR).
    """
    pass
