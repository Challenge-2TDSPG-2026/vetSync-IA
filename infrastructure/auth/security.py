import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# Pegamos a MESMA chave secreta que o Spring Security do Java usa
# Deve estar no seu arquivo .env
SECRET_KEY = os.getenv("AUTH_JWT_SECRET", "chave_secreta_padrao_para_desenvolvimento")
ALGORITHM = "HS256" # Geralmente o Spring usa HS256 por padrão

def verificar_token_externo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Decodifica e valida o token JWT gerado pelo Java Spring Security.
    """
    token = credentials.credentials
    
    try:
        # Decodifica o token. Se a assinatura não bater ou estiver expirado, vai dar erro.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # O Spring geralmente salva o nome do usuário na propriedade 'sub' (subject) do JWT
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
