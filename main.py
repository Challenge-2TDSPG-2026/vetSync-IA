from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.routers import router
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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
