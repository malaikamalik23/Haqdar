# Haqdar API image, with the AI modules, the procedure packs and the search model inside.
# Build from the project root:
#   docker build -f backend/Dockerfile -t haqdar-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/tmp \
    HF_HOME=/opt/hf \
    HF_HUB_DISABLE_TELEMETRY=1 \
    OMP_NUM_THREADS=2 \
    HAQDAR_AI_MODE=real \
    HAQDAR_PACKS_DIR=/app/packs \
    HAQDAR_EMBED_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# The app runs as an unprivileged user with no home folder and no login shell.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Tesseract reads the text from photos of notices (Urdu and English).
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-urd \
    && rm -rf /var/lib/apt/lists/*

# 1. PyTorch, CPU version only. The default build is several times larger and needs a GPU.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. The other libraries. setuptools is upgraded because the copy that ships with the base image
#    bundles libraries with known vulnerabilities.
COPY backend/requirements.txt backend/ai/requirements-runtime.txt ./
# hadolint ignore=DL3013
RUN pip install --no-cache-dir -r requirements.txt -r requirements-runtime.txt \
    && pip install --no-cache-dir --upgrade setuptools

# 3. Download the search model now, so the container needs no internet when it runs.
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['HAQDAR_EMBED_MODEL'])"
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Code and packs are copied as root and stay read-only for the app user.
COPY backend/main.py ./
COPY backend/security ./security
COPY backend/ai ./ai
COPY packs ./packs

USER 10001:10001
EXPOSE 8000

# The server only starts answering after the model is loaded, hence the long start period.
HEALTHCHECK --interval=30s --timeout=3s --start-period=120s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
