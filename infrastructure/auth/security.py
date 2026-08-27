from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verificar_token_externo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependência que valida o token JWT recebido no cabeçalho Authorization.
    Aqui você deve implementar a lógica para validar o token no sistema externo,
    ou verificar a assinatura JWT (se possuir a chave pública).
    """
    token = credentials.credentials
    
    # TODO: Implementar a validação real do token externo
    token_valido = True # Substitua por sua lógica de validação
    
    if not token_valido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retorne os dados do usuário se precisar
    return {"token": token, "user_id": "id_do_usuario_externo"}
