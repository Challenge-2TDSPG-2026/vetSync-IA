import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

def validar_token(token: str) -> dict:
    """Valida um Bearer emitido pelo Java e preserva-o para o repasse à agenda."""
    secret_key = os.getenv("AUTH_JWT_SECRET")
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_JWT_SECRET não está configurado para validar o token recebido."
        )

    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        usuario_logado = payload.get("sub")
        if usuario_logado is None:
            raise HTTPException(status_code=401, detail="Token inválido: Usuário não encontrado no payload")
        return {"token": token, "username": usuario_logado, "payload_completo": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O token de autenticação expirou",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verificar_token_externo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Decodifica e valida o token JWT gerado pelo Java Spring Security (se em prod).
    Em desenvolvimento sem Bearer, mantém um usuário isolado para endpoints
    que não precisam falar com o Java. Se houver Bearer, ele é sempre validado
    e preservado para a integração local com a agenda.
    """
    ambiente = os.getenv("APP_ENV", "dev")

    if not credentials and ambiente == "dev":
        return {"token": "mock_token_dev", "username": "usuario_dev", "payload_completo": {"roles": ["ADMIN"]}}

    if not credentials:
        raise HTTPException(status_code=403, detail="Não autenticado. Token não fornecido.")

    return validar_token(credentials.credentials)
