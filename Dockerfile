FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ARG SENTENCE_TRANSFORMERS_MODEL

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${SENTENCE_TRANSFORMERS_MODEL}')"

COPY scripts/indexer.py .

CMD ["python", "indexer.py"]