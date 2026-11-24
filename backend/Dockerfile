# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .
# RepoPilot runs inference on CPU in the EC2 demo. Resolve the CPU-only PyTorch
# wheel and project requirements in one pip operation; otherwise pip can select
# multi-gigabyte NVIDIA/CUDA dependencies while resolving sentence-transformers.
RUN pip install --no-cache-dir --prefix=/install \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      torch==2.5.1+cpu \
      -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install git for cloning repos
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
