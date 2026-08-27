from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.assistant_routers import router, triage_router, checkin_router
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="API Assistente Veterinário de Pós-Atendimento",
    description="Serviço para interpretar comandos em linguagem natural e estruturar planos de pós-atendimento.",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(triage_router)
app.include_router(checkin_router)

# Importando e incluindo as novas rotas que conectam IA + Banco Oracle
from presentation.routers.agendamentos_router import router as agendamentos_oracle_router
from presentation.routers.atendimentos_router import router as atendimentos_oracle_router
from presentation.routers.triagens_router import router as triagens_oracle_router
from presentation.routers.checkin_router import router as checkin_oracle_router
from presentation.routers.orquestrador_router import router as orquestrador_router

app.include_router(agendamentos_oracle_router)
app.include_router(atendimentos_oracle_router)
app.include_router(triagens_oracle_router)
app.include_router(checkin_oracle_router)
app.include_router(orquestrador_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
