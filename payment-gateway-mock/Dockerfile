FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app/ ./app/

# Expor porta
EXPOSE 8001

# Comando para rodar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
