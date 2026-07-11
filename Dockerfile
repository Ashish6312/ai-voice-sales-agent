FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first to avoid pulling 2 GB of CUDA drivers
RUN pip install --no-cache-dir \
    torch \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install the remaining project dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install --retries 10 --default-timeout 100 -r requirements.txt

COPY . .

RUN mkdir -p audio/input audio/output logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]