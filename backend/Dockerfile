FROM python:3.11-slim

WORKDIR /app

# Instala dependências (camada cacheada separada do código)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Baixa e cacheia o modelo durante o build — sem depender de volume
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Código da aplicação
COPY backend/app ./app
COPY backend/worker ./worker

# CSV do Qualis necessário pelo etl_pipeline.py
COPY data/qualis/qualis_capes.csv ./data/qualis/qualis_capes.csv

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
