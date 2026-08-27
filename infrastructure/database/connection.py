import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lê o ambiente atual (dev ou prod)
APP_ENV = os.getenv("APP_ENV", "dev")

if APP_ENV == "prod":
    # Em Produção, usamos a Oracle
    # O formato Oracle: oracle+oracledb://usuario:senha@host:porta/?service_name=nome_do_servico
    DATABASE_URL = os.getenv("ORACLE_DB_URL", "oracle+oracledb://user:pass@localhost:1521/?service_name=XEPDB1")
else:
    # Em Desenvolvimento, usamos o SQLite local na própria pasta
    DATABASE_URL = "sqlite:///./dev_database.db"


# Como o banco já existe, o engine não vai criar as tabelas, apenas conectar.
if APP_ENV == "prod":
    engine = create_engine(DATABASE_URL, echo=True)
else:
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Importar modelos para que o SQLAlchemy saiba que eles existem antes de criar as tabelas
from . import models

# Em desenvolvimento, como o SQLite começa vazio, podemos pedir pro SQLAlchemy criar as tabelas
if APP_ENV == "dev":
    Base.metadata.create_all(bind=engine)

# Dependência do FastAPI para injetar a sessão do banco de dados nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
