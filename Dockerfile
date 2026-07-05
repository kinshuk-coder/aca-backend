FROM python:3.11-slim

# 1. Install system dependencies as root
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy and install requirements using uv while still root
COPY requirements.txt .
RUN pip install uv && uv pip install --system --no-cache-dir -r requirements.txt

# 3. Create a non-root user (Hugging Face requirement)
RUN useradd -m -u 1000 user

# 4. Create the sandbox directory and change ownership to the non-root user
RUN mkdir -p /app/ai_workspace && chown -R user:user /app

# 5. Switch to the non-root user for security
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 6. Copy the remaining app code and ensure it belongs to the non-root user
COPY --chown=user:user . .

# 7. Expose the mandatory Hugging Face port
EXPOSE 7860

# 8. Start Uvicorn pointing to port 7860
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]