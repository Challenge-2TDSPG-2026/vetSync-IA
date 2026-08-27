from sqlalchemy import Column, Integer, String, Date, Boolean
from infrastructure.database.connection import Base

# Como o banco é mantido por outra pessoa e já existe, 
# precisamos mapear EXATAMENTE os nomes das tabelas e colunas que existem lá no Oracle.
# Não use create_all(). Apenas defina a estrutura para o SQLAlchemy saber ler e escrever.

class AgendamentoOracle(Base):
    __tablename__ = "AGENDAMENTO" # Nome exato da tabela no Oracle
    
    # Se o schema no Oracle for específico, você pode usar:
    # __table_args__ = {'schema': 'NOME_DO_SCHEMA'}

    id = Column("ID_AGENDAMENTO", Integer, primary_key=True, index=True)
    # Adicione as demais colunas exatas...
    # status = Column("STATUS_AGENDA", String)
    # data_consulta = Column("DATA_CONSULTA", Date)
    pass
