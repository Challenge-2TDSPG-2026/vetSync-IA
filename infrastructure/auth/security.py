import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("AUTH_JWT_SECRET", "chave_secreta_padrao_para_desenvolvimento")
ALGORITHM = "HS256" 

def verificar_token_externo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Decodifica e valida o token JWT gerado pelo Java Spring Security (se em prod).
    Se em ambiente de desenvolvimento (dev), pula a autenticação.
    """
    ambiente = os.getenv("APP_ENV", "dev")
    
    if ambiente == "dev":
        return {"token": "mock_token_dev", "username": "usuario_dev", "payload_completo": {"roles": ["ADMIN"]}}

    if not credentials:
        raise HTTPException(status_code=403, detail="Não autenticado. Token não fornecido.")

    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
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
