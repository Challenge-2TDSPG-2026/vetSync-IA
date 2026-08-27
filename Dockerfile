# Usar uma imagem oficial leve do Python
FROM python:3.11-slim

# Impedir que o Python crie arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Impedir que os logs fiquem em buffer
ENV PYTHONUNBUFFERED=1

# Configurar o diretório de trabalho dentro do container
WORKDIR /app

# Copiar apenas o requirements primeiro, para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o restante do código para o container
COPY . .

# O Google Cloud Run por padrão injeta a variável PORT (geralmente 8080)
ENV PORT=8080

# Expor a porta 8080 (documentação)
EXPOSE 8080

# Comando para rodar a aplicação usando Uvicorn e ouvindo na variável PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
