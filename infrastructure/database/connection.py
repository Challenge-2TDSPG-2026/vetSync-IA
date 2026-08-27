import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# A string de conexão Oracle geralmente tem o formato:
# oracle+oracledb://usuario:senha@host:porta/?service_name=nome_do_servico
DATABASE_URL = os.getenv("ORACLE_DB_URL", "oracle+oracledb://user:pass@localhost:1521/?service_name=XEPDB1")

# Como o banco já existe, o engine não vai criar as tabelas, apenas conectar.
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependência do FastAPI para injetar a sessão do banco de dados nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
