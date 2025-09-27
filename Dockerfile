# Minimal container for Cloud Run
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY app/data ./app/data

ENV PORT=8080
ENV MODE=online

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
