FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir ai_workspace

COPY requirements.txt .

RUN pip install uv

RUN uv pip install --system --no-cache-dir -r requirements.txt

COPY . .


CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]